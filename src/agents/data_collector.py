"""
Data Collector Agent.

This agent collects customer feedback from multiple sources including reviews,
support tickets, and surveys. It loads data from sample files or generates
mock data when needed.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console

from .base_agent import BaseAgent


class DataCollectorAgent(BaseAgent):
    """
    Data Collection Specialist agent that gathers and normalizes customer feedback.

    Collects data from reviews, support tickets, and surveys, either from sample files
    or by generating realistic mock data. Provides summary statistics and colored output.
    """

    def __init__(self):
        """Initialize the Data Collector Agent with appropriate system prompt."""
        system_prompt = (
            "You are a Data Collection Specialist who gathers and normalizes customer feedback "
            "from reviews, support tickets, and surveys. Focus on accuracy, data quality, "
            "and consistent formatting."
        )

        super().__init__(
            name="data_collector",
            role="Data Collection Specialist",
            system_prompt=system_prompt,
            temperature=0.3  # Lower temperature for more consistent data handling
        )

        self.console = Console()
        self.data_dir = Path("data/sample")

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the workflow state to collect customer feedback data.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with collected data and summary
        """
        try:
            self.console.print("\n[bold blue]📊 Data Collection Agent Starting...[/bold blue]")

            company = state.get("company_name", "Unknown Company")
            product = state.get("product_name", "Unknown Product")
            data_sources = state.get("data_sources", [])

            self.console.print(f"Collecting data for [green]{company}[/green] - [yellow]{product}[/yellow]")
            self.console.print(f"Sources to process: [cyan]{', '.join(data_sources)}[/cyan]\n")

            # Collect data from each source
            all_collected_data = []
            for source in data_sources:
                self.console.print(f"🔍 Processing [bold]{source}[/bold]...", end=" ")
                source_data = self._collect_from_source(source, company, product)

                if source_data:
                    self.console.print(f"[green]✓ {len(source_data)} records collected[/green]")
                    all_collected_data.extend(source_data)
                else:
                    self.console.print("[red]✗ No data found[/red]")

            # Generate summary statistics
            data_summary = self._generate_summary(all_collected_data)

            # Update state
            state["raw_data"] = all_collected_data
            state["data_summary"] = data_summary
            state["current_step"] = "data_collection_completed"
            state["iteration_count"] += 1

            self.console.print("\n[bold green]✅ Data Collection Complete![/bold green]")
            self.console.print(f"Total records collected: [bold cyan]{len(all_collected_data)}[/bold cyan]")

            # Display summary
            self._display_summary(data_summary)

            return state

        except Exception as e:
            error_msg = f"Data collection failed: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            self.console.print(f"[bold red]❌ Error: {error_msg}[/bold red]")
            return state

    def _collect_from_source(self, source: str, company: str, product: str) -> List[Dict[str, Any]]:
        """
        Collect data from a specific source, loading from file or generating mock data.

        Args:
            source: Data source name ('reviews', 'support_tickets', 'surveys')
            company: Company name for context
            product: Product name for context

        Returns:
            List of data records
        """
        # Map source names to file names
        file_mapping = {
            "reviews": "reviews.json",
            "tickets": "support_tickets.json",
            "surveys": "surveys.json"
        }

        filename = file_mapping.get(source, f"{source}.json")
        file_path = self.data_dir / filename

        # Try to load from file first
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.logger.info(f"Loaded {len(data)} records from {filename}")
                return data
            except Exception as e:
                self.logger.warning(f"Failed to load {filename}: {e}. Generating mock data.")

        # Generate mock data if file doesn't exist or failed to load
        return self._generate_mock_data(source, company, product)

    def _generate_mock_data(self, source: str, company: str, product: str, count: int = 20) -> List[Dict[str, Any]]:
        """
        Generate realistic mock customer feedback data.

        Args:
            source: Data source type ('reviews', 'tickets', 'surveys')
            company: Company name
            product: Product name
            count: Number of records to generate

        Returns:
            List of mock data records
        """
        mock_data = []

        for i in range(count):
            record_id = "04d"
            base_date = datetime.now() - timedelta(days=random.randint(1, 90))

            if source == "reviews":
                # Generate review data
                rating = random.randint(1, 5)
                titles = [
                    "Excellent product!", "Good value", "Could be better", "Not satisfied",
                    "Amazing quality", "Poor customer service", "Fast shipping", "Slow delivery",
                    "Highly recommend", "Would not buy again"
                ]
                reviews = [
                    f"The {product} from {company} works great and exceeded my expectations.",
                    f"Good quality product but the price is a bit high for what you get.",
                    f"I've had issues with this product. Customer service was not helpful.",
                    f"Fast shipping and excellent packaging. Very satisfied with my purchase.",
                    f"The product arrived damaged. Took forever to get a replacement.",
                    f"Best purchase I've made this year. Highly recommend to others.",
                    f"Average product. Does what it says but nothing special.",
                    f"Terrible experience. Will not be buying from this company again.",
                    f"Quality is outstanding. Worth every penny.",
                    f"Product is okay but the instructions were confusing."
                ]

                record = {
                    "id": f"review_{record_id}",
                    "source": "mock_review_platform",
                    "rating": rating,
                    "title": random.choice(titles),
                    "text": random.choice(reviews),
                    "date": base_date.strftime("%Y-%m-%d"),
                    "verified_purchase": random.choice([True, False]),
                    "helpful_votes": random.randint(0, 50)
                }

            elif source in ["tickets", "support_tickets"]:
                # Generate support ticket data
                categories = ["shipping", "product_quality", "billing", "returns", "technical_support"]
                priorities = ["low", "medium", "high"]
                statuses = ["resolved", "pending", "closed"]

                subjects = [
                    f"Delay in shipping order #{record_id}",
                    f"Issue with {product} quality",
                    "Billing question about recent purchase",
                    "Return request for defective item",
                    "Technical support needed"
                ]

                descriptions = [
                    f"I ordered the {product} two weeks ago but haven't received it yet. Can you provide an update?",
                    f"The {product} I received doesn't work as expected. It's defective.",
                    "I was charged twice for my order. Can you refund the duplicate charge?",
                    f"I need to return the {product} as it's not what I expected. How do I proceed?",
                    f"I'm having trouble setting up the {product}. The instructions are unclear."
                ]

                record = {
                    "id": f"ticket_{record_id}",
                    "subject": random.choice(subjects),
                    "description": random.choice(descriptions),
                    "category": random.choice(categories),
                    "priority": random.choice(priorities),
                    "status": random.choice(statuses),
                    "created_date": base_date.strftime("%Y-%m-%d"),
                    "customer_satisfaction": random.randint(1, 5) if random.choice([True, False]) else None
                }

            elif source == "surveys":
                # Generate survey data
                survey_types = ["post_purchase", "satisfaction", "feedback"]

                record = {
                    "id": f"survey_{record_id}",
                    "survey_type": random.choice(survey_types),
                    "responses": {
                        "overall_satisfaction": random.randint(1, 5),
                        "likely_to_recommend": random.randint(1, 5),
                        "value_for_money": random.randint(1, 5),
                        "product_quality": random.randint(1, 5),
                        "customer_service": random.randint(1, 5)
                    },
                    "comments": f"Good experience with {product} from {company}. Would recommend to friends." if random.choice([True, False]) else "",
                    "date": base_date.strftime("%Y-%m-%d")
                }

            mock_data.append(record)

        self.logger.info(f"Generated {len(mock_data)} mock records for {source}")
        return mock_data

    def _generate_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics from collected data.

        Args:
            data: List of all collected data records

        Returns:
            Dictionary with summary statistics
        """
        total_records = len(data)

        # Count by source
        source_counts = {}
        ratings = []
        dates = []

        for record in data:
            # Count sources
            source = record.get("source", "unknown")
            if source not in source_counts:
                source_counts[source] = 0
            source_counts[source] += 1

            # Collect ratings
            rating = (record.get("rating") or
                     record.get("overall_satisfaction") or
                     record.get("customer_satisfaction"))
            if rating and isinstance(rating, (int, float)):
                ratings.append(rating)

            # Collect dates
            date_str = (record.get("date") or
                       record.get("created_date"))
            if date_str:
                try:
                    dates.append(datetime.fromisoformat(date_str))
                except:
                    pass  # Skip invalid dates

        # Calculate rating statistics
        rating_stats = {}
        if ratings:
            rating_stats = {
                "average_rating": round(sum(ratings) / len(ratings), 2),
                "min_rating": min(ratings),
                "max_rating": max(ratings),
                "total_ratings": len(ratings),
                "rating_distribution": {
                    str(i): ratings.count(i) for i in range(1, 6)
                }
            }

        # Calculate date range
        date_range = {}
        if dates:
            date_range = {
                "earliest": min(dates).strftime("%Y-%m-%d"),
                "latest": max(dates).strftime("%Y-%m-%d"),
                "date_span_days": (max(dates) - min(dates)).days
            }

        return {
            "total_records": total_records,
            "records_by_source": source_counts,
            "rating_statistics": rating_stats,
            "date_range": date_range,
            "data_sources_processed": len(source_counts)
        }

    def _display_summary(self, summary: Dict[str, Any]):
        """Display a formatted summary using rich console."""
        self.console.print("\n[bold cyan]📈 Collection Summary:[/bold cyan]")
        self.console.print(f"  Total Records: [bold yellow]{summary['total_records']}[/bold yellow]")

        if summary['records_by_source']:
            self.console.print("  Records by Source:")
            for source, count in summary['records_by_source'].items():
                self.console.print(f"    {source}: [green]{count}[/green]")

        if summary['rating_statistics']:
            stats = summary['rating_statistics']
            self.console.print(f"  Average Rating: [bold magenta]{stats['average_rating']:.1f}[/bold magenta] ⭐")
            self.console.print(f"  Rating Range: {stats['min_rating']}-{stats['max_rating']}")

        if summary['date_range']:
            date_range = summary['date_range']
            self.console.print(f"  Date Range: {date_range['earliest']} to {date_range['latest']}")
            self.console.print(f"  Date Span: {date_range['date_span_days']} days")
