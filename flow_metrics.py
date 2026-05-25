#!/usr/bin/env python3
"""
Azure DevOps Flow Metrics Dashboard

Extracts common flow metrics from Azure DevOps Analytics OData API:
- Throughput: Work items completed per time period
- Cycle Time: Time from work started to completed
- Lead Time: Time from creation to completion
- WIP: Work in progress by state
- Velocity: Items delivered per sprint/week
- Cumulative Flow Diagram (CFD) data

Usage:
    python flow_metrics.py
"""

import argparse
import os
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from ado_odata_async import AdoODataClient
from ado_odata_async.query import Apply, Filter

# Override OData version for compatibility with PAT access level
import ado_odata_async.client as client_mod
client_mod.ODATA_VERSION = "v2.0"

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricResult(BaseModel):
    """Structured metric result"""
    metric_name: str
    value: float
    unit: str
    period: str
    calculated_at: datetime = Field(default_factory=datetime.now)


class FlowMetrics:
    """Extract and calculate flow metrics from Azure DevOps Analytics"""
    
    def __init__(self, org: str, project: str, pat: str):
        self.org = org
        self.project = project
        self.pat = pat
        self.client: AdoODataClient | None = None
        
    async def __aenter__(self):
        """Initialize client with proper context manager"""
        self.client = AdoODataClient(
            org=self.org,
            project=self.project,
            pat=self.pat
        )
        await self.client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc, tb):
        """Clean up client"""
        if self.client:
            await self.client.__aexit__(exc_type, exc, tb)
    
    async def get_throughput(self, days: int = 30) -> MetricResult:
        """Calculate throughput: items completed per day"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # WorkItemSnapshot requires groupby(DateSK) per HR-13
        result = await (
            self.client.query("WorkItemSnapshot")
            .apply(
                Apply()
                .filter(
                    Filter.and_(
                        Filter.ge("DateSK", start_date.strftime("%Y-%m-%d")),
                        Filter.le("DateSK", end_date.strftime("%Y-%m-%d")),
                        Filter.eq("State", "Done")
                    )
                )
                .groupby("DateSK", "State")
                .aggregate("Count", "WorkItemId")
            )
            .get()
        )
        
        # Calculate daily throughput
        total_completed = 0
        for item in result.get("value", []):
            total_completed += item.get("Count", 0)
        
        daily_throughput = total_completed / days if days > 0 else 0
        
        return MetricResult(
            metric_name="Throughput",
            value=daily_throughput,
            unit="items/day",
            period=f"Last {days} days"
        )
    
    async def get_cycle_time(self, days: int = 30) -> MetricResult:
        """Calculate average cycle time: days from created to completed"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query WorkItems with created and completed dates
        result = await (
            self.client.query("WorkItems")
            .filter(
                Filter.and_(
                    Filter.ge("CreatedDate", start_date.strftime("%Y-%m-%dT%H:%M:%SZ")),
                    Filter.le("CreatedDate", end_date.strftime("%Y-%m-%dT%H:%M:%SZ")),
                    Filter.not_(Filter.eq("State", "New"))  # Exclude unstarted work
                )
            )
            .select("WorkItemId", "Title", "State", "CreatedDate", "ClosedDate")
            .top(1000)  # Limit sample size
            .get()
        )
        
        total_cycle_time = 0
        completed_items = 0
        
        for item in result.get("value", []):
            created_date = item.get("CreatedDate")
            closed_date = item.get("ClosedDate")
            
            if created_date and closed_date and item.get("State") == "Done":
                created = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                completed = datetime.fromisoformat(closed_date.replace('Z', '+00:00'))
                cycle_time = (completed - created).days
                total_cycle_time += cycle_time
                completed_items += 1
        
        avg_cycle_time = total_cycle_time / completed_items if completed_items > 0 else 0
        
        return MetricResult(
            metric_name="Cycle Time",
            value=avg_cycle_time,
            unit="days",
            period=f"Last {days} days"
        )
    
    async def get_lead_time(self, days: int = 30) -> MetricResult:
        """Calculate average lead time: days from created to delivered"""
        # Lead time is same as cycle time for this implementation
        return await self.get_cycle_time(days)
    
    async def get_wip_by_state(self) -> dict[str, int]:
        """Get Work in Progress by state"""
        result = await (
            self.client.query("WorkItems")
            .filter(Filter.not_(Filter.eq("State", "Done")))  # Exclude completed
            .select("State")
            .top(5000)
            .get()
        )
        
        wip_by_state = defaultdict(int)
        for item in result.get("value", []):
            state = item.get("State", "Unknown")
            wip_by_state[state] += 1
        
        return dict(wip_by_state)
    
    async def get_velocity(self, weeks: int = 4) -> MetricResult:
        """Calculate velocity: items completed per week"""
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        result = await (
            self.client.query("WorkItemSnapshot")
            .apply(
                Apply()
                .filter(
                    Filter.and_(
                        Filter.ge("DateSK", start_date.strftime("%Y-%m-%d")),
                        Filter.le("DateSK", end_date.strftime("%Y-%m-%d")),
                        Filter.eq("State", "Done")
                    )
                )
                .groupby("DateSK")
                .aggregate("Count", "WorkItemId")
            )
            .get()
        )
        
        # Calculate weekly velocity
        total_completed = 0
        for item in result.get("value", []):
            total_completed += item.get("Count", 0)
        
        weekly_velocity = total_completed / weeks if weeks > 0 else 0
        
        return MetricResult(
            metric_name="Velocity",
            value=weekly_velocity,
            unit="items/week",
            period=f"Last {weeks} weeks"
        )
    
    async def get_cfd_data(self, days: int = 30) -> dict[str, list[int]]:
        """Get Cumulative Flow Diagram data by state"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all states
        states_result = await (
            self.client.query("WorkItems")
            .select("State")
            .top(1)
            .get()
        )
        
        all_states = set()
        for item in states_result.get("value", []):
            all_states.add(item.get("State", "Unknown"))
        
        # Get daily counts by state
        cfd_data = {state: [] for state in all_states}
        cfd_data["Date"] = []
        
        for i in range(days):
            current_date = end_date - timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            
            cfd_data["Date"].append(i)
            
            try:
                result = await (
                    self.client.query("WorkItemSnapshot")
                    .apply(
                        Apply()
                        .filter(
                            Filter.and_(
                                Filter.ge("DateSK", date_str),
                                Filter.le("DateSK", date_str),
                                Filter.eq("State", "Done")
                            )
                        )
                        .groupby("DateSK", "State")  # Required for HR-13
                .aggregate("Count", "sum")  # Count rows

                    )
                    .get()
                )
            except AdoODataError as e:
                raise ValueError(f"API Error: {str(e)}") from e
            
            # Initialize all states to 0
            for state in all_states:
                cfd_data[state].append(0)
            
            # Update actual counts
            for item in result.get("value", []):
                state = item.get("State", "Unknown")
                count = item.get("Count", 0)
                if state in cfd_data:
                    # Reverse the order for CFD (oldest first)
                    cfd_data[state][-(i+1)] = count
        
        return cfd_data


async def main():
    """Main execution function"""
    # Check if credentials are available
    org = os.getenv("AZURE_DEVOPS_ORG")
    project = os.getenv("AZURE_DEVOPS_PROJECT")
    pat = os.getenv("AZURE_DEVOPS_PAT")
    
    if not all([org, project, pat]):
        print("❌ Missing required environment variables. Check .env file:")
        print("   AZURE_DEVOPS_ORG")
        print("   AZURE_DEVOPS_PROJECT") 
        print("   AZURE_DEVOPS_PAT")
        return
    
    print(f"🚀 Fetching flow metrics for {org}/{project}")
    print("=" * 50)
    
    async with FlowMetrics(org, project, pat) as metrics:
        # Calculate all metrics
        throughput = await metrics.get_throughput()
        cycle_time = await metrics.get_cycle_time()
        lead_time = await metrics.get_lead_time()
        velocity = await metrics.get_velocity()
        wip_by_state = await metrics.get_wip_by_state()
        
        print("\n📊 FLOW METRICS")
        print("-" * 30)
        print(f"📈 Throughput: {throughput.value:.2f} {throughput.unit}")
        print(f"🔄 Cycle Time: {cycle_time.value:.1f} {cycle_time.unit}")
        print(f"⏱️  Lead Time: {lead_time.value:.1f} {lead_time.unit}")
        print(f"🎯 Velocity: {velocity.value:.2f} {velocity.unit}")
        
        print("\n📋 WORK IN PROGRESS")
        print("-" * 30)
        total_wip = sum(wip_by_state.values())
        for state, count in wip_by_state.items():
            percentage = (count / total_wip * 100) if total_wip > 0 else 0
            print(f"  {state}: {count} ({percentage:.1f}%)")
        print(f"  Total WIP: {total_wip}")
        
        print("\n📈 CUMULATIVE FLOW DIAGRAM")
        print("-" * 30)
        cfd_data = await metrics.get_cfd_data(days=7)  # Last 7 days
        print("  Date    | " + " | ".join(f"{state[:8]:>8}" for state in cfd_data.keys() if state != "Date"))
        
        for i, date_offset in enumerate(cfd_data["Date"]):
            date_str = (datetime.now() - timedelta(days=date_offset)).strftime("%m-%d")
            row_data = [date_str]
            
            for state in cfd_data.keys():
                if state != "Date":
                    row_data.append(f"{cfd_data[state][i]:>8}")
            
            print("  " + " | ".join(row_data))
        
        print(f"\n🎯 Summary:")
        print(f"  • Team is completing {throughput.value:.1f} items per day")
        print(f"  • Average time from start to finish: {cycle_time.value:.1f} days")
        print(f"  • {total_wip} items currently in progress")
        print(f"  • Weekly delivery rate: {velocity.value:.1f} items/week")


if __name__ == "__main__":
    asyncio.run(main())