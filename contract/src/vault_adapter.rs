/// RWA Vault Adapter Interface
///
/// Defines the contract interface for RWA (Real World Assets) vault deposits and yield.
/// Implementations handle fund custody, yield accrual, and share-based withdrawals.

use soroban_sdk::{Address, contracterror};

/// Errors returned by vault operations
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum VaultError {
    /// Deposit operation failed (vault unavailable, insufficient capacity, etc.)
    DepositFailed = 1,
    /// Withdrawal operation failed (vault unavailable, insufficient funds, etc.)
    WithdrawalFailed = 2,
    /// Requested share count is invalid or caller doesn't hold specified shares
    InvalidShares = 3,
}

/// Result type for vault operations
pub type VaultResult<T> = Result<T, VaultError>;

/// Trait for RWA vault adapters
///
/// A vault adapter handles deposit of game entry fees and withdrawal of prize pools,
/// potentially accruing yield over the duration of the game. This adapter pattern
/// allows the arena to work with multiple vault implementations (primary, fallback, test mocks).
pub trait RwaVaultAdapter {
    /// Deposit funds into the vault, receiving shares in exchange.
    ///
    /// # Arguments
    /// * `amount` - Amount in stroops (1 XLM = 10_000_000 stroops) to deposit
    ///
    /// # Returns
    /// Number of shares issued for the deposit. Shares represent a claim on the principal
    /// plus any accrued yield. The relationship is:
    /// - shares = amount / yield_multiplier (at deposit time)
    /// - withdrawal_amount = shares * yield_multiplier (at withdrawal time)
    ///
    /// # Errors
    /// * [`VaultError::DepositFailed`] - Vault rejected the deposit
    fn deposit(&self, amount: i128) -> VaultResult<u64>;

    /// Withdraw funds from the vault by burning shares.
    ///
    /// # Arguments
    /// * `shares` - Number of shares to burn and withdraw
    ///
    /// # Returns
    /// Amount in stroops received (principal + accrued yield):
    /// - returned_amount = shares * yield_multiplier
    ///
    /// # Errors
    /// * [`VaultError::WithdrawalFailed`] - Vault rejected the withdrawal
    /// * [`VaultError::InvalidShares`] - Caller doesn't hold the specified shares
    fn withdraw(&self, shares: u64) -> VaultResult<i128>;

    /// Query the current yield multiplier.
    ///
    /// # Returns
    /// Yield multiplier as a fixed-point u64 (e.g., 1_000_000 = 1.0x, 1_050_000 = 1.05x for 5% yield)
    ///
    /// # Precision
    /// - 1_000_000 represents 1.0x (no yield)
    /// - Multipliers > 1_000_000 indicate positive yield
    /// - Multipliers < 1_000_000 indicate losses (unexpected but possible in crisis scenarios)
    /// - Example: 1_050_000 = 5% APY
    fn query_yield_multiplier(&self) -> VaultResult<u64>;
}

/// Helper for fixed-point arithmetic on yield multipliers
///
/// All multipliers use u64 with implicit 6-decimal fixed point:
/// - 1_000_000 = 1.0x
/// - 500_000 = 0.5x
/// - 1_500_000 = 1.5x
pub mod fixed_point {
    pub const SCALE: u64 = 1_000_000;

    /// Calculate shares from amount using yield multiplier
    /// shares = (amount * SCALE) / multiplier
    pub fn amount_to_shares(amount: i128, multiplier: u64) -> u64 {
        ((amount as u128 * SCALE as u128) / multiplier as u128) as u64
    }

    /// Calculate amount from shares using yield multiplier
    /// amount = (shares * multiplier) / SCALE
    pub fn shares_to_amount(shares: u64, multiplier: u64) -> i128 {
        ((shares as u128 * multiplier as u128) / SCALE as u128) as i128
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fixed_point_no_yield() {
        // No yield: multiplier = 1.0x
        let multiplier = 1_000_000u64;
        let amount = 100_000_000i128; // 10 XLM in stroops

        let shares = fixed_point::amount_to_shares(amount, multiplier);
        assert_eq!(shares, amount as u64, "No yield: shares = amount");

        let returned = fixed_point::shares_to_amount(shares, multiplier);
        assert_eq!(returned, amount, "No yield: amount = shares");
    }

    #[test]
    fn test_fixed_point_5_percent_yield() {
        // 5% yield: multiplier = 1.05x
        let multiplier = 1_050_000u64;
        let amount = 100_000_000i128; // 10 XLM in stroops

        let shares = fixed_point::amount_to_shares(amount, multiplier);
        // shares ≈ 100_000_000 / 1.05 ≈ 95_238_095
        assert!(shares < amount as u64, "Yield > 1.0x: shares < amount");

        let returned = fixed_point::shares_to_amount(shares, multiplier);
        // returned ≈ 95_238_095 * 1.05 ≈ 100_000_000 (within rounding)
        assert!(
            (returned - amount).abs() <= 2,
            "Rounding error <= 2 stroops: {} vs {}",
            returned,
            amount
        );
    }

    #[test]
    fn test_fixed_point_loss_scenario() {
        // Loss: multiplier = 0.99x (edge case, shouldn't happen in normal operations)
        let multiplier = 990_000u64;
        let amount = 100_000_000i128;

        let shares = fixed_point::amount_to_shares(amount, multiplier);
        // shares = 100_000_000 / 0.99 ≈ 101_010_101
        assert!(shares > amount as u64, "Loss: shares > amount");

        let returned = fixed_point::shares_to_amount(shares, multiplier);
        // returned ≈ 101_010_101 * 0.99 ≈ 100_000_000
        assert!(
            (returned - amount).abs() <= 2,
            "Loss scenario: rounding error <= 2 stroops"
        );
    }
}
