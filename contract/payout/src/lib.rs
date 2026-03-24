#![no_std]
use soroban_sdk::{contract, contractimpl, Env};

#[contract]
pub struct PayoutContract;

#[contractimpl]
impl PayoutContract {
    /// Placeholder function — returns a fixed value for contract liveness checks.
    ///
    /// # Arguments
    /// * `env` - The Soroban environment.
    ///
    /// # Authorization
    /// None — open to any caller.
    pub fn hello(env: Env) -> u32 {
        789
    }
}

#[cfg(test)]
mod test;
