"""
SLA compliance checker for load test results.

Validates that load test results meet performance targets.
"""

import sys
import csv
from typing import Dict, List


class SLAChecker:
    """Check if load test results meet SLA requirements."""
    
    # Performance targets (milliseconds)
    TARGETS = {
        "p50": 200,    # 50th percentile < 200ms
        "p95": 1000,   # 95th percentile < 1000ms
        "p99": 2000,   # 99th percentile < 2000ms
        "error_rate": 1.0,  # < 1% error rate
    }
    
    def __init__(self, csv_file: str):
        """Initialize with results CSV file."""
        self.csv_file = csv_file
        self.violations: List[str] = []
    
    def load_results(self) -> Dict[str, Dict]:
        """Load results from CSV file."""
        results = {}
        
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Type'] == 'Aggregated':
                    continue
                
                name = row['Name']
                results[name] = {
                    'requests': int(row['Request Count']),
                    'failures': int(row['Failure Count']),
                    'p50': float(row['50%']),
                    'p95': float(row['95%']),
                    'p99': float(row['99%']),
                    'avg': float(row['Average Response Time']),
                    'min': float(row['Min Response Time']),
                    'max': float(row['Max Response Time']),
                }
        
        return results
    
    def check_latency(self, results: Dict[str, Dict]) -> bool:
        """Check latency targets."""
        passed = True
        
        for endpoint, stats in results.items():
            # Check P50
            if stats['p50'] > self.TARGETS['p50']:
                self.violations.append(
                    f"❌ {endpoint}: P50 {stats['p50']:.0f}ms > target {self.TARGETS['p50']}ms"
                )
                passed = False
            
            # Check P95
            if stats['p95'] > self.TARGETS['p95']:
                self.violations.append(
                    f"❌ {endpoint}: P95 {stats['p95']:.0f}ms > target {self.TARGETS['p95']}ms"
                )
                passed = False
            
            # Check P99
            if stats['p99'] > self.TARGETS['p99']:
                self.violations.append(
                    f"❌ {endpoint}: P99 {stats['p99']:.0f}ms > target {self.TARGETS['p99']}ms"
                )
                passed = False
        
        return passed
    
    def check_error_rate(self, results: Dict[str, Dict]) -> bool:
        """Check error rate targets."""
        passed = True
        
        for endpoint, stats in results.items():
            if stats['requests'] == 0:
                continue
            
            error_rate = (stats['failures'] / stats['requests']) * 100
            
            if error_rate > self.TARGETS['error_rate']:
                self.violations.append(
                    f"❌ {endpoint}: Error rate {error_rate:.2f}% > target {self.TARGETS['error_rate']}%"
                )
                passed = False
        
        return passed
    
    def print_summary(self, results: Dict[str, Dict]) -> None:
        """Print test summary."""
        print("\n" + "=" * 80)
        print("LOAD TEST RESULTS SUMMARY")
        print("=" * 80 + "\n")
        
        # Overall stats
        total_requests = sum(s['requests'] for s in results.values())
        total_failures = sum(s['failures'] for s in results.values())
        overall_error_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
        
        print(f"Total Requests: {total_requests:,}")
        print(f"Total Failures: {total_failures:,}")
        print(f"Overall Error Rate: {overall_error_rate:.2f}%")
        print()
        
        # Per-endpoint stats
        print("Per-Endpoint Performance:")
        print("-" * 80)
        print(f"{'Endpoint':<50} {'P50':>8} {'P95':>8} {'P99':>8} {'Errors':>8}")
        print("-" * 80)
        
        for endpoint, stats in sorted(results.items()):
            error_rate = (stats['failures'] / stats['requests'] * 100) if stats['requests'] > 0 else 0
            print(
                f"{endpoint:<50} "
                f"{stats['p50']:>7.0f}ms "
                f"{stats['p95']:>7.0f}ms "
                f"{stats['p99']:>7.0f}ms "
                f"{error_rate:>7.2f}%"
            )
        
        print("-" * 80)
    
    def run(self) -> int:
        """Run SLA compliance check."""
        try:
            results = self.load_results()
            
            if not results:
                print("❌ No results found in CSV file")
                return 1
            
            self.print_summary(results)
            
            # Run checks
            latency_ok = self.check_latency(results)
            error_ok = self.check_error_rate(results)
            
            # Print violations
            if self.violations:
                print("\n⚠️  SLA VIOLATIONS DETECTED:\n")
                for violation in self.violations:
                    print(violation)
                print()
            
            # Final verdict
            if latency_ok and error_ok:
                print("✅ All SLA targets met!")
                return 0
            else:
                print("❌ SLA targets not met")
                return 1
        
        except FileNotFoundError:
            print(f"❌ Results file not found: {self.csv_file}")
            return 1
        except Exception as e:
            print(f"❌ Error checking SLA: {e}")
            return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_sla.py <results_stats.csv>")
        sys.exit(1)
    
    checker = SLAChecker(sys.argv[1])
    sys.exit(checker.run())
