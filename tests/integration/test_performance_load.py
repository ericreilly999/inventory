"""
Performance and load tests for inventory management system.

Tests API response times and throughput, validates system behavior
under concurrent load.
Requirements: 10.4
"""

import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List

import pytest
import requests


@dataclass
class PerformanceMetrics:
    """Container for performance test metrics."""

    response_times: List[float]
    success_count: int
    error_count: int
    throughput: float  # requests per second
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float


class PerformanceTestRunner:
    """Helper class for running performance tests."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth_token = None

    def authenticate(self) -> bool:
        """Authenticate and get access token."""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=10,
            )

            if response.status_code == 200:
                self.auth_token = response.json().get("access_token")
                return True
            return False
        except requests.RequestException:
            return False

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a timed HTTP request."""
        url = f"{self.base_url}{endpoint}"
        headers = self.get_auth_headers()
        headers.update(kwargs.get("headers", {}))

        start_time = time.time()
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=kwargs.get("timeout", 30),
                **{k: v for k, v in kwargs.items() if k not in ["headers", "timeout"]},
            )

            end_time = time.time()
            response_time = end_time - start_time

            return {
                "success": True,
                "status_code": response.status_code,
                "response_time": response_time,
                "response_size": (len(response.content) if response.content else 0),
            }

        except requests.RequestException as e:
            end_time = time.time()
            response_time = end_time - start_time

            return {
                "success": False,
                "error": str(e),
                "response_time": response_time,
                "response_size": 0,
            }

    def run_concurrent_requests(
        self, request_func, num_requests: int, max_workers: int = 10
    ) -> PerformanceMetrics:
        """Run concurrent requests and collect metrics."""
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all requests
            futures = [executor.submit(request_func) for _ in range(num_requests)]

            # Collect results
            start_time = time.time()
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(
                        {
                            "success": False,
                            "error": str(e),
                            "response_time": 0,
                            "response_size": 0,
                        }
                    )
            end_time = time.time()

        # Calculate metrics
        response_times = [r["response_time"] for r in results]
        success_count = sum(1 for r in results if r["success"])
        error_count = len(results) - success_count

        total_time = end_time - start_time
        throughput = len(results) / total_time if total_time > 0 else 0

        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = (
            statistics.quantiles(response_times, n=20)[18]
            if len(response_times) >= 20
            else 0
        )
        p99_response_time = (
            statistics.quantiles(response_times, n=100)[98]
            if len(response_times) >= 100
            else 0
        )

        return PerformanceMetrics(
            response_times=response_times,
            success_count=success_count,
            error_count=error_count,
            throughput=throughput,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
        )


class TestAPIPerformance:
    """Test API response times and performance characteristics."""

    @pytest.fixture
    def perf_runner(self):
        """Create performance test runner."""
        runner = PerformanceTestRunner()
        if not runner.authenticate():
            pytest.skip("Authentication failed - API not available")
        return runner

    def test_single_request_response_times(self, perf_runner: PerformanceTestRunner):
        """Test individual API endpoint response times."""

        endpoints = [
            ("GET", "/api/v1/items/parent"),
            ("GET", "/api/v1/items/child"),
            ("GET", "/api/v1/locations"),
            ("GET", "/api/v1/reports/inventory"),
            ("GET", "/api/v1/users"),
        ]

        for method, endpoint in endpoints:
            result = perf_runner.make_request(method, endpoint)

            if result["success"]:
                # Response time should be under 2 seconds for single requests
                assert result["response_time"] < 2.0, (
                    f"{method} {endpoint} took "
                    f"{result['response_time']:.3f}s (> 2.0s)"
                )

                # Should return successful status codes
                assert (
                    200 <= result["status_code"] < 300
                ), f"{method} {endpoint} returned status {result['status_code']}"
            else:
                pytest.skip(f"Endpoint {endpoint} not available: {result.get('error')}")

    def test_concurrent_read_operations(self, perf_runner: PerformanceTestRunner):
        """Test concurrent read operations performance."""

        def read_inventory():
            return perf_runner.make_request("GET", "/api/v1/items/parent")

        # Test with 20 concurrent requests
        metrics = perf_runner.run_concurrent_requests(
            read_inventory, 20, max_workers=10
        )

        # At least 80% of requests should succeed
        success_rate = metrics.success_count / (
            metrics.success_count + metrics.error_count
        )
        assert success_rate >= 0.8, f"Success rate {success_rate:.2%} < 80%"

        # Average response time should be reasonable
        assert (
            metrics.avg_response_time < 5.0
        ), f"Average response time {metrics.avg_response_time:.3f}s > 5.0s"

        # P95 response time should be acceptable
        if metrics.p95_response_time > 0:
            assert (
                metrics.p95_response_time < 10.0
            ), f"P95 response time {metrics.p95_response_time:.3f}s > 10.0s"

    def test_mixed_read_write_operations(self, perf_runner: PerformanceTestRunner):
        """Test mixed read/write operations under load."""

        def mixed_operations():
            # Randomly choose between read and write operations
            import random

            operations = [
                ("GET", "/api/v1/items/parent"),
                ("GET", "/api/v1/locations"),
                (
                    "POST",
                    "/api/v1/items/parent",
                    {
                        "json": {
                            "name": f"Test Item {random.randint(1000, 9999)}",
                            "description": "Load test item",
                            "item_type_id": "test-type-id",
                            "current_location_id": "test-location-id",
                        }
                    },
                ),
            ]

            method, endpoint, *args = random.choice(operations)
            kwargs = args[0] if args else {}

            return perf_runner.make_request(method, endpoint, **kwargs)

        # Test with 15 concurrent mixed operations
        metrics = perf_runner.run_concurrent_requests(
            mixed_operations, 15, max_workers=8
        )

        # Should handle mixed load reasonably well
        success_rate = metrics.success_count / (
            metrics.success_count + metrics.error_count
        )
        assert (
            success_rate >= 0.6
        ), f"Mixed operations success rate {success_rate:.2%} < 60%"

        # Throughput should be reasonable
        assert (
            metrics.throughput > 0.5
        ), f"Throughput {metrics.throughput:.2f} req/s < 0.5 req/s"

    def test_database_query_performance(self, perf_runner: PerformanceTestRunner):
        """Test database-intensive operations performance."""

        def query_reports():
            return perf_runner.make_request("GET", "/api/v1/reports/inventory")

        def query_move_history():
            return perf_runner.make_request("GET", "/api/v1/movements/history")

        # Test report generation performance
        report_metrics = perf_runner.run_concurrent_requests(
            query_reports, 10, max_workers=5
        )

        if report_metrics.success_count > 0:
            # Report queries should complete within reasonable time
            assert report_metrics.avg_response_time < 15.0, (
                f"Report query avg time "
                f"{report_metrics.avg_response_time:.3f}s > 15.0s"
            )

        # Test move history queries
        history_metrics = perf_runner.run_concurrent_requests(
            query_move_history, 10, max_workers=5
        )

        if history_metrics.success_count > 0:
            # History queries should be reasonably fast
            assert history_metrics.avg_response_time < 10.0, (
                f"History query avg time "
                f"{history_metrics.avg_response_time:.3f}s > 10.0s"
            )


class TestLoadTesting:
    """Test system behavior under various load conditions."""

    @pytest.fixture
    def perf_runner(self):
        """Create performance test runner."""
        runner = PerformanceTestRunner()
        if not runner.authenticate():
            pytest.skip("Authentication failed - API not available")
        return runner

    def test_sustained_load(self, perf_runner: PerformanceTestRunner):
        """Test system behavior under sustained load."""

        def sustained_requests():
            endpoints = [
                "/api/v1/items/parent",
                "/api/v1/locations",
                "/api/v1/users",
            ]

            import random

            endpoint = random.choice(endpoints)
            return perf_runner.make_request("GET", endpoint)

        # Run sustained load for 30 requests over multiple batches
        batch_size = 10
        num_batches = 3
        all_metrics = []

        for batch in range(num_batches):
            metrics = perf_runner.run_concurrent_requests(
                sustained_requests, batch_size, max_workers=5
            )
            all_metrics.append(metrics)

            # Small delay between batches
            time.sleep(1)

        # Analyze sustained performance
        total_requests = sum(m.success_count + m.error_count for m in all_metrics)
        total_successes = sum(m.success_count for m in all_metrics)

        if total_requests > 0:
            overall_success_rate = total_successes / total_requests
            assert (
                overall_success_rate >= 0.7
            ), f"Sustained load success rate {overall_success_rate:.2%} < 70%"

        # Performance should not degrade significantly across batches
        if len(all_metrics) >= 2:
            first_batch_avg = all_metrics[0].avg_response_time
            last_batch_avg = all_metrics[-1].avg_response_time

            if first_batch_avg > 0:
                degradation_ratio = last_batch_avg / first_batch_avg
                assert degradation_ratio < 3.0, (
                    f"Performance degraded by {degradation_ratio:.1f}x "
                    f"under sustained load"
                )

    def test_burst_load_handling(self, perf_runner: PerformanceTestRunner):
        """Test system handling of burst traffic."""

        def burst_request():
            return perf_runner.make_request("GET", "/api/v1/items/parent")

        # Test burst of 25 concurrent requests
        burst_metrics = perf_runner.run_concurrent_requests(
            burst_request, 25, max_workers=15
        )

        # System should handle burst without complete failure
        if burst_metrics.success_count + burst_metrics.error_count > 0:
            success_rate = burst_metrics.success_count / (
                burst_metrics.success_count + burst_metrics.error_count
            )
            assert (
                success_rate >= 0.5
            ), f"Burst load success rate {success_rate:.2%} < 50%"

        # No request should take extremely long
        if burst_metrics.response_times:
            max_response_time = max(burst_metrics.response_times)
            assert (
                max_response_time < 30.0
            ), f"Max response time {max_response_time:.3f}s > 30.0s during burst"

    def test_error_rate_under_load(self, perf_runner: PerformanceTestRunner):
        """Test error rates under increasing load."""

        def load_request():
            return perf_runner.make_request("GET", "/api/v1/items/parent")

        # Test with different load levels
        load_levels = [5, 10, 15]
        error_rates = []

        for load_level in load_levels:
            metrics = perf_runner.run_concurrent_requests(
                load_request, load_level, max_workers=min(load_level, 10)
            )

            total_requests = metrics.success_count + metrics.error_count
            if total_requests > 0:
                error_rate = metrics.error_count / total_requests
                error_rates.append(error_rate)

            # Brief pause between load tests
            time.sleep(0.5)

        # Error rate should not increase dramatically with load
        if len(error_rates) >= 2:
            max_error_rate = max(error_rates)
            assert (
                max_error_rate < 0.5
            ), f"Error rate {max_error_rate:.2%} > 50% under load"

    def test_memory_leak_detection(self, perf_runner: PerformanceTestRunner):
        """Test for potential memory leaks under repeated requests."""

        def repeated_request():
            return perf_runner.make_request("GET", "/api/v1/items/parent")

        # Run multiple rounds of requests to detect memory issues
        rounds = 5
        requests_per_round = 8
        response_times = []

        for round_num in range(rounds):
            metrics = perf_runner.run_concurrent_requests(
                repeated_request, requests_per_round, max_workers=4
            )

            if metrics.avg_response_time > 0:
                response_times.append(metrics.avg_response_time)

            # Short delay between rounds
            time.sleep(2)

        # Response times should not increase significantly over time
        if len(response_times) >= 3:
            first_third_avg = statistics.mean(
                response_times[: len(response_times) // 3]
            )
            last_third_avg = statistics.mean(
                response_times[-len(response_times) // 3 :]
            )

            if first_third_avg > 0:
                time_increase_ratio = last_third_avg / first_third_avg
                assert (
                    time_increase_ratio < 2.5
                ), f"Response time increased {
                    time_increase_ratio:.1f}x - possible memory leak"


class TestConcurrencyHandling:
    """Test concurrent access patterns and race conditions."""

    @pytest.fixture
    def perf_runner(self):
        """Create performance test runner."""
        runner = PerformanceTestRunner()
        if not runner.authenticate():
            pytest.skip("Authentication failed - API not available")
        return runner

    def test_concurrent_item_creation(self, perf_runner: PerformanceTestRunner):
        """Test concurrent item creation for race conditions."""

        def create_item(item_suffix):
            return perf_runner.make_request(
                "POST",
                "/api/v1/items/parent",
                json={
                    "name": f"Concurrent Item {item_suffix}",
                    "description": f"Created concurrently {item_suffix}",
                    "item_type_id": "test-type-id",
                    "current_location_id": "test-location-id",
                },
            )

        # Create items concurrently
        results = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(create_item, i) for i in range(12)]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"success": False, "error": str(e)})

        # Analyze results for race conditions
        successful_creates = [
            r for r in results if r["success"] and r.get("status_code") in [200, 201]
        ]

        # Should handle concurrent creates without major issues
        if len(results) > 0:
            success_rate = len(successful_creates) / len(results)
            # Allow for some failures due to validation or constraints
            assert (
                success_rate >= 0.3
            ), f"Concurrent creation success rate {success_rate:.2%} < 30%"

    def test_concurrent_item_updates(self, perf_runner: PerformanceTestRunner):
        """Test concurrent updates to the same resources."""

        # First, try to get an existing item
        get_result = perf_runner.make_request("GET", "/api/v1/items/parent")

        if not get_result["success"]:
            pytest.skip("Cannot get items for concurrent update test")

        def update_item(update_suffix):
            return perf_runner.make_request(
                "PUT",
                "/api/v1/items/parent/test-item-id",
                json={
                    "name": f"Updated Item {update_suffix}",
                    "description": f"Updated concurrently {update_suffix}",
                },
            )

        # Attempt concurrent updates
        results = []
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(update_item, i) for i in range(8)]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"success": False, "error": str(e)})

        # System should handle concurrent updates gracefully
        # (may reject some due to optimistic locking or return 404 for non-existent item)
        if len(results) > 0:
            non_error_results = [r for r in results if r["success"]]
            # At least some requests should be handled properly
            assert (
                len(non_error_results) >= len(results) * 0.2
            ), "System failed to handle any concurrent updates properly"

    def test_read_write_concurrency(self, perf_runner: PerformanceTestRunner):
        """Test concurrent read and write operations."""

        def read_operation():
            return perf_runner.make_request("GET", "/api/v1/items/parent")

        def write_operation(suffix):
            return perf_runner.make_request(
                "POST",
                "/api/v1/items/parent",
                json={
                    "name": f"RW Test Item {suffix}",
                    "description": "Read-write concurrency test",
                    "item_type_id": "test-type-id",
                    "current_location_id": "test-location-id",
                },
            )

        # Mix of read and write operations
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit mix of reads and writes
            futures = []
            for i in range(15):
                if i % 3 == 0:  # 1/3 writes, 2/3 reads
                    futures.append(executor.submit(write_operation, i))
                else:
                    futures.append(executor.submit(read_operation))

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"success": False, "error": str(e)})

        # Analyze read/write concurrency handling
        if len(results) > 0:
            successful_ops = [r for r in results if r["success"]]
            success_rate = len(successful_ops) / len(results)

            # Should handle mixed read/write load reasonably
            assert (
                success_rate >= 0.4
            ), f"Read/write concurrency success rate {success_rate:.2%} < 40%"
