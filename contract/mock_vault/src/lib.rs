#![no_std]

use soroban_sdk::{
    Address, Env, Symbol, contract, contracterror, contractimpl, contracttype,
    symbol_short,
};

// ── Storage keys ──────────────────────────────────────────────────────────────

const YIELD_MULTIPLIER_KEY: Symbol = symbol_short!("YIELD_MUL");
const TOTAL_SHARES_KEY: Symbol = symbol_short!("TOT_SHARE");
const TOTAL_DEPOSITED_KEY: Symbol = symbol_short!("TOT_DEP");

// ── Error codes ───────────────────────────────────────────────────────────────

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum VaultError {
    /// Deposit operation failed
    DepositFailed = 1,
    /// Withdrawal operation failed
    WithdrawalFailed = 2,
    /// Invalid shares amount
    InvalidShares = 3,
}

// ── Types ─────────────────────────────────────────────────────────────────────

#[contracttype]
#[derive(Clone, Debug)]
pub enum DataKey {
    /// Player's share balance: DataKey::PlayerShares(Address) -> u64
    PlayerShares(Address),
}

// ── Constants ─────────────────────────────────────────────────────────────────

/// Default yield multiplier: 1.0x (no yield)
const DEFAULT_YIELD_MULTIPLIER: u64 = 1_000_000;

/// Fixed-point scale for yield calculations
const SCALE: u64 = 1_000_000;

// ── Contract ──────────────────────────────────────────────────────────────────

#[contract]
pub struct MockYieldVault;

#[contractimpl]
impl MockYieldVault {
    /// Initialize vault with admin authority (for test configuration)
    ///
    /// In production, this would set authorized parties. In tests,
    /// we keep it simple and allow direct configuration.
    pub fn initialize(env: Env) {
        // Set default yield multiplier (no yield initially)
        env.storage()
            .instance()
            .set(&YIELD_MULTIPLIER_KEY, &DEFAULT_YIELD_MULTIPLIER);
        env.storage().instance().set(&TOTAL_SHARES_KEY, &0u64);
        env.storage()
            .instance()
            .set(&TOTAL_DEPOSITED_KEY, &0i128);
    }

    /// Deposit funds into the vault, receiving shares.
    ///
    /// Shares = (amount * SCALE) / yield_multiplier
    /// If yield_multiplier = 1_000_000 (1.0x), then shares = amount
    /// If yield_multiplier = 1_050_000 (1.05x), then shares < amount (less shares for same amount)
    pub fn deposit(env: Env, player: Address, amount: i128) -> Result<u64, VaultError> {
        if amount <= 0 {
            return Err(VaultError::DepositFailed);
        }

        let multiplier = Self::get_yield_multiplier(env.clone());

        // Calculate shares: (amount * SCALE) / multiplier
        let shares = ((amount as u128 * SCALE as u128) / multiplier as u128) as u64;

        if shares == 0 {
            return Err(VaultError::DepositFailed);
        }

        // Update total shares
        let total_shares: u64 = env
            .storage()
            .instance()
            .get(&TOTAL_SHARES_KEY)
            .unwrap_or(0u64);
        env.storage()
            .instance()
            .set(&TOTAL_SHARES_KEY, &(total_shares + shares));

        // Update total deposited
        let total_deposited: i128 = env
            .storage()
            .instance()
            .get(&TOTAL_DEPOSITED_KEY)
            .unwrap_or(0i128);
        env.storage()
            .instance()
            .set(&TOTAL_DEPOSITED_KEY, &(total_deposited + amount));

        // Store player's share balance
        let player_shares: u64 = env
            .storage()
            .instance()
            .get::<_, u64>(&DataKey::PlayerShares(player.clone()))
            .unwrap_or(0u64);
        env.storage()
            .instance()
            .set(&DataKey::PlayerShares(player), &(player_shares + shares));

        Ok(shares)
    }

    /// Withdraw funds from vault by burning shares.
    ///
    /// Amount = (shares * multiplier) / SCALE
    /// If yield_multiplier = 1_050_000 (1.05x yield), amount = shares * 1.05
    pub fn withdraw(env: Env, player: Address, shares: u64) -> Result<i128, VaultError> {
        if shares == 0 {
            return Err(VaultError::InvalidShares);
        }

        // Check player has sufficient shares
        let player_shares: u64 = env
            .storage()
            .instance()
            .get::<_, u64>(&DataKey::PlayerShares(player.clone()))
            .unwrap_or(0u64);

        if player_shares < shares {
            return Err(VaultError::InvalidShares);
        }

        let multiplier = Self::get_yield_multiplier(env.clone());

        // Calculate amount: (shares * multiplier) / SCALE
        let amount = ((shares as u128 * multiplier as u128) / SCALE as u128) as i128;

        if amount <= 0 {
            return Err(VaultError::WithdrawalFailed);
        }

        // Update total shares
        let total_shares: u64 = env
            .storage()
            .instance()
            .get(&TOTAL_SHARES_KEY)
            .unwrap_or(0u64);
        env.storage()
            .instance()
            .set(&TOTAL_SHARES_KEY, &(total_shares.saturating_sub(shares)));

        // Update player's balance
        env.storage()
            .instance()
            .set(&DataKey::PlayerShares(player), &(player_shares - shares));

        Ok(amount)
    }

    /// Get current yield multiplier
    pub fn get_yield_multiplier(env: Env) -> u64 {
        env.storage()
            .instance()
            .get(&YIELD_MULTIPLIER_KEY)
            .unwrap_or(DEFAULT_YIELD_MULTIPLIER)
    }

    /// Set yield multiplier (test-only configuration)
    ///
    /// # Arguments
    /// * `multiplier` - Fixed-point yield multiplier (1_000_000 = 1.0x, 1_050_000 = 5% yield)
    pub fn set_yield_multiplier(env: Env, multiplier: u64) -> Result<(), VaultError> {
        if multiplier == 0 {
            return Err(VaultError::DepositFailed);
        }

        env.storage()
            .instance()
            .set(&YIELD_MULTIPLIER_KEY, &multiplier);
        Ok(())
    }

    /// Query total shares outstanding (for verification)
    pub fn get_total_shares(env: Env) -> u64 {
        env.storage()
            .instance()
            .get(&TOTAL_SHARES_KEY)
            .unwrap_or(0u64)
    }

    /// Query total deposited amount (for verification)
    pub fn get_total_deposited(env: Env) -> i128 {
        env.storage()
            .instance()
            .get(&TOTAL_DEPOSITED_KEY)
            .unwrap_or(0i128)
    }

    /// Query player's current share balance
    pub fn get_player_shares(env: Env, player: Address) -> u64 {
        env.storage()
            .instance()
            .get::<_, u64>(&DataKey::PlayerShares(player))
            .unwrap_or(0u64)
    }
}
