with open("payout/src/lib.rs", "r") as f:
    text = f.read()

text = text.replace(
"""pub struct SplitPayoutReceipt {
    pub arena_id: u32,
    pub winner: Address,
    pub amount: i128,
    pub currency: Address,
pub struct PayoutReceipt {""",
"""pub struct SplitPayoutReceipt {
    pub arena_id: u32,
    pub winner: Address,
    pub amount: i128,
    pub currency: Address,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PayoutReceipt {"""
)

with open("payout/src/lib.rs", "w") as f:
    f.write(text)

