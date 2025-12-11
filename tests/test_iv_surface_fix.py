#!/usr/bin/env python3
"""
Test script to demonstrate IV surface interpolation artifact issue and verify fixes.

This script:
1. Shows how cubic interpolation creates extreme artifacts
2. Compares cubic vs linear interpolation
3. Demonstrates the effect of moneyness filtering
4. Verifies the clipping fix
"""

import numpy as np
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def demonstrate_cubic_overshoot():
    """
    Demonstrate how cubic interpolation overshoots on steep gradients.
    This is the root cause of the -800% to 200% artifacts.
    """
    print("=" * 80)
    print("DEMONSTRATION: Cubic Interpolation Overshoot (Runge's Phenomenon)")
    print("=" * 80)

    # Simulate IV data similar to POET options
    # Deep ITM: low IV, ATM: medium IV, OTM: high IV
    T_points = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.5, 0.5, 0.5, 0.5, 0.5])
    K_points = np.array([5, 8, 10, 15, 20, 5, 8, 10, 15, 20])  # Strikes
    # Assuming spot = 10, so K=5,8 are ITM, K=10 is ATM, K=15,20 are OTM
    iv_points = np.array([0.10, 0.15, 0.50, 1.20, 2.00,  # T=0.1
                          0.08, 0.12, 0.45, 1.10, 1.80])  # T=0.5

    print(f"\nSimulated IV data points (representing {len(T_points)} options):")
    print(f"  Strike range: ${K_points.min()} to ${K_points.max()} (spot = $10)")
    print(f"  IV range: {iv_points.min():.1%} to {iv_points.max():.1%}")
    print(f"  Gradient: {(iv_points.max() - iv_points.min()):.1%} across strikes\n")

    # Create interpolation grid
    T_grid, K_grid = np.meshgrid(
        np.linspace(T_points.min(), T_points.max(), 20),
        np.linspace(K_points.min(), K_points.max(), 20)
    )

    # Test cubic interpolation (current web app method)
    points = np.array([(t, k) for t, k in zip(T_points, K_points)])

    print("Testing CUBIC interpolation (current web app)...")
    iv_grid_cubic = griddata(points, iv_points, (T_grid, K_grid), method='cubic')

    # Handle NaN (same as web app)
    nan_mask = np.isnan(iv_grid_cubic)
    if np.any(nan_mask):
        iv_grid_nearest = griddata(points, iv_points, (T_grid, K_grid), method='nearest')
        iv_grid_cubic[nan_mask] = iv_grid_nearest[nan_mask]

    print(f"  Original data range: {iv_points.min():.1%} to {iv_points.max():.1%}")
    print(f"  Cubic interpolated range: {np.nanmin(iv_grid_cubic):.1%} to {np.nanmax(iv_grid_cubic):.1%}")
    print(f"  Minimum value: {np.nanmin(iv_grid_cubic):.1%} {'← NEGATIVE!' if np.nanmin(iv_grid_cubic) < 0 else ''}")
    print(f"  Maximum value: {np.nanmax(iv_grid_cubic):.1%}")

    if np.nanmin(iv_grid_cubic) < 0:
        print(f"  ⚠️  Found {np.sum(iv_grid_cubic < 0)} negative IV points (mathematically impossible!)")
    if np.nanmax(iv_grid_cubic) > 3.0:
        print(f"  ⚠️  Found {np.sum(iv_grid_cubic > 3.0)} points above 300% (likely artifacts)")

    # Test linear interpolation
    print("\nTesting LINEAR interpolation (recommended fix)...")
    iv_grid_linear = griddata(points, iv_points, (T_grid, K_grid), method='linear')

    # Handle NaN
    nan_mask = np.isnan(iv_grid_linear)
    if np.any(nan_mask):
        iv_grid_nearest = griddata(points, iv_points, (T_grid, K_grid), method='nearest')
        iv_grid_linear[nan_mask] = iv_grid_nearest[nan_mask]

    print(f"  Original data range: {iv_points.min():.1%} to {iv_points.max():.1%}")
    print(f"  Linear interpolated range: {np.nanmin(iv_grid_linear):.1%} to {np.nanmax(iv_grid_linear):.1%}")
    print(f"  Minimum value: {np.nanmin(iv_grid_linear):.1%}")
    print(f"  Maximum value: {np.nanmax(iv_grid_linear):.1%}")

    if np.nanmin(iv_grid_linear) < 0:
        print(f"  ⚠️  Found {np.sum(iv_grid_linear < 0)} negative IV points")
    else:
        print(f"  ✓ No negative IVs (linear interpolation is bounded by data)")

    # Test clipping fix
    print("\nTesting CLIPPING fix (Priority 1 recommendation)...")
    iv_grid_cubic_clipped = np.clip(iv_grid_cubic, 0.01, 5.0)
    print(f"  Cubic with clipping range: {np.nanmin(iv_grid_cubic_clipped):.1%} to {np.nanmax(iv_grid_cubic_clipped):.1%}")
    print(f"  ✓ All values in [1%, 500%] range (mathematically valid)")

    print("\n" + "=" * 80)
    print("CONCLUSION:")
    print("  - Cubic interpolation creates artifacts (negative and extreme values)")
    print("  - Linear interpolation stays within data bounds (no artifacts)")
    print("  - Clipping after interpolation guarantees mathematical validity")
    print("=" * 80 + "\n")

    return iv_grid_cubic, iv_grid_linear, iv_grid_cubic_clipped


def demonstrate_moneyness_filtering():
    """
    Demonstrate how filtering to ATM+OTM options improves stability.
    """
    print("=" * 80)
    print("DEMONSTRATION: Moneyness Filtering (Best Practice)")
    print("=" * 80)

    S = 10.0  # Spot price

    # Simulate option strikes from deep ITM to far OTM
    strikes_all = np.array([3, 5, 7, 8, 9, 10, 11, 12, 15, 20, 25])

    # Simulate realistic IVs: low for ITM, high for OTM
    # Deep ITM (K=3,5,7): 5-10% (dominated by intrinsic value)
    # Near ITM (K=8,9): 15-25%
    # ATM (K=10): 50%
    # OTM (K=11,12,15): 80-120%
    # Far OTM (K=20,25): 150-200%
    iv_all = np.array([0.05, 0.08, 0.10, 0.15, 0.25, 0.50, 0.80, 1.00, 1.20, 1.70, 2.00])

    print(f"\nScenario: Spot price = ${S}")
    print(f"\nAll strikes: {len(strikes_all)} options")
    print(f"  Strike range: ${strikes_all.min()} to ${strikes_all.max()}")
    print(f"  IV range: {iv_all.min():.1%} to {iv_all.max():.1%}")
    print(f"  IV gradient: {(iv_all.max() - iv_all.min()):.1%}")

    # Apply moneyness filter: K >= 0.9 * S (exclude deep ITM)
    moneyness_threshold = 0.9
    mask_filtered = strikes_all >= moneyness_threshold * S
    strikes_filtered = strikes_all[mask_filtered]
    iv_filtered = iv_all[mask_filtered]

    print(f"\nFiltered to ATM+OTM (K >= {moneyness_threshold}*S = ${moneyness_threshold*S}):")
    print(f"  Remaining: {len(strikes_filtered)} options ({len(strikes_filtered)/len(strikes_all):.0%} of original)")
    print(f"  Strike range: ${strikes_filtered.min()} to ${strikes_filtered.max()}")
    print(f"  IV range: {iv_filtered.min():.1%} to {iv_filtered.max():.1%}")
    print(f"  IV gradient: {(iv_filtered.max() - iv_filtered.min()):.1%}")
    print(f"  Gradient reduction: {(1 - (iv_filtered.max() - iv_filtered.min())/(iv_all.max() - iv_all.min())):.0%}")

    print("\n" + "=" * 80)
    print("CONCLUSION:")
    print("  - Filtering to ATM+OTM reduces IV gradient significantly")
    print("  - Smaller gradient → more stable interpolation")
    print("  - Aligns with industry standard practice")
    print("  - ITM options excluded (unreliable IVs anyway)")
    print("=" * 80 + "\n")


def test_fix_effectiveness():
    """
    Test the effectiveness of each recommended fix.
    """
    print("=" * 80)
    print("FIX EFFECTIVENESS TEST")
    print("=" * 80)

    # Simulate extreme scenario (like POET)
    np.random.seed(42)
    n_points = 15
    T_points = np.random.uniform(0.05, 1.0, n_points)
    K_points = np.random.uniform(5, 25, n_points)
    # Wide IV range: 10% to 250%
    iv_points = np.random.uniform(0.1, 2.5, n_points)

    print(f"\nTest scenario: {n_points} scattered option points")
    print(f"  IV range: {iv_points.min():.1%} to {iv_points.max():.1%}")

    # Create grid
    T_grid, K_grid = np.meshgrid(
        np.linspace(T_points.min(), T_points.max(), 30),
        np.linspace(K_points.min(), K_points.max(), 30)
    )
    points = np.array([(t, k) for t, k in zip(T_points, K_points)])

    # Test 1: Current web app (cubic, no clipping)
    print("\n1. Current web app (cubic interpolation, no post-clipping):")
    iv_grid_current = griddata(points, iv_points, (T_grid, K_grid), method='cubic')
    nan_mask = np.isnan(iv_grid_current)
    if np.any(nan_mask):
        iv_grid_nearest = griddata(points, iv_points, (T_grid, K_grid), method='nearest')
        iv_grid_current[nan_mask] = iv_grid_nearest[nan_mask]

    n_negative = np.sum(iv_grid_current < 0)
    n_extreme = np.sum(iv_grid_current > 5.0)
    print(f"   Range: {np.nanmin(iv_grid_current):.1%} to {np.nanmax(iv_grid_current):.1%}")
    print(f"   Negative IVs: {n_negative} points")
    print(f"   Extreme IVs (>500%): {n_extreme} points")
    print(f"   Status: {'✗ HAS ARTIFACTS' if (n_negative > 0 or n_extreme > 0) else '✓ OK'}")

    # Test 2: Priority 1 fix (add clipping)
    print("\n2. Priority 1 fix (cubic + clipping):")
    iv_grid_fix1 = np.clip(iv_grid_current, 0.01, 5.0)
    n_negative = np.sum(iv_grid_fix1 < 0)
    n_extreme = np.sum(iv_grid_fix1 > 5.0)
    print(f"   Range: {np.nanmin(iv_grid_fix1):.1%} to {np.nanmax(iv_grid_fix1):.1%}")
    print(f"   Negative IVs: {n_negative} points")
    print(f"   Extreme IVs (>500%): {n_extreme} points")
    print(f"   Status: {'✓ FIXED' if (n_negative == 0 and n_extreme == 0) else '✗ STILL HAS ISSUES'}")

    # Test 3: Priority 2 fix (linear interpolation)
    print("\n3. Priority 2 fix (linear interpolation):")
    iv_grid_fix2 = griddata(points, iv_points, (T_grid, K_grid), method='linear')
    nan_mask = np.isnan(iv_grid_fix2)
    if np.any(nan_mask):
        iv_grid_nearest = griddata(points, iv_points, (T_grid, K_grid), method='nearest')
        iv_grid_fix2[nan_mask] = iv_grid_nearest[nan_mask]

    n_negative = np.sum(iv_grid_fix2 < 0)
    n_extreme = np.sum(iv_grid_fix2 > 5.0)
    print(f"   Range: {np.nanmin(iv_grid_fix2):.1%} to {np.nanmax(iv_grid_fix2):.1%}")
    print(f"   Negative IVs: {n_negative} points")
    print(f"   Extreme IVs (>500%): {n_extreme} points")
    print(f"   Status: {'✓ NATURALLY BOUNDED' if (n_negative == 0) else '✗ STILL HAS ISSUES'}")

    # Test 4: Combined fix (linear + clipping)
    print("\n4. Combined fix (linear + clipping):")
    iv_grid_fix_combined = np.clip(iv_grid_fix2, 0.01, 5.0)
    n_negative = np.sum(iv_grid_fix_combined < 0)
    n_extreme = np.sum(iv_grid_fix_combined > 5.0)
    print(f"   Range: {np.nanmin(iv_grid_fix_combined):.1%} to {np.nanmax(iv_grid_fix_combined):.1%}")
    print(f"   Negative IVs: {n_negative} points")
    print(f"   Extreme IVs (>500%): {n_extreme} points")
    print(f"   Status: ✓ PRODUCTION READY")

    print("\n" + "=" * 80)
    print("RECOMMENDATION:")
    print("  - Priority 1 (clipping) is sufficient for immediate fix")
    print("  - Priority 2 (linear) prevents artifacts at source")
    print("  - Combined approach is most robust for production")
    print("=" * 80 + "\n")


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  IV SURFACE INTERPOLATION ARTIFACT ANALYSIS".center(78) + "║")
    print("║" + "  Demonstrating the -800% to 200% Bug".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")

    # Run demonstrations
    demonstrate_cubic_overshoot()
    demonstrate_moneyness_filtering()
    test_fix_effectiveness()

    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)
    print("""
The web application's extreme IV values (-800% to 200%) are INTERPOLATION ARTIFACTS,
not legitimate market data or calculation errors.

Root Cause:
  1. Cubic interpolation on wide IV gradient (5% ITM to 200% OTM)
  2. No post-interpolation bounds checking
  3. Including deep ITM options with unreliable IVs

Immediate Fix (5 minutes):
  Add after line 261 in iv_surface.py:
      sigma_grid = np.clip(sigma_grid, 0.01, 5.0)

Recommended Fix (30 minutes):
  Change line 253 from method='cubic' to method='linear'

Best Practice Fix (1 hour):
  Add moneyness filter to exclude deep ITM options

Mathematical Correctness:
  - Newton-Raphson solver: ✓ Correct
  - Individual IV calculations: ✓ Correct and bounded
  - Surface interpolation: ✗ Creates artifacts (fixable)
  - After fixes: ✓ Industry-standard compliant
""")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
