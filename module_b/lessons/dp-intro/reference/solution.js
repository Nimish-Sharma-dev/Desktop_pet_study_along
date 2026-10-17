function climbStairs(n) {
  let a = 1;
  let b = 1;
  for (let i = 0; i < n; i++) {
    [a, b] = [b, a + b];
  }
  return a;
}

function minCoins(coins, amount) {
  const inf = amount + 1;
  const dp = new Array(amount + 1).fill(inf);
  dp[0] = 0;
  for (let a = 1; a <= amount; a++) {
    for (const c of coins) {
      if (c <= a && dp[a - c] + 1 < dp[a]) dp[a] = dp[a - c] + 1;
    }
  }
  return dp[amount] !== inf ? dp[amount] : -1;
}

module.exports = { climbStairs, minCoins };
