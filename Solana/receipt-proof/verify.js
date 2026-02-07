const { Connection, clusterApiUrl, PublicKey } = require("@solana/web3.js");

const MEMO_PROGRAM_ID = new PublicKey(
  "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
);

// Simple base58-ish signature check (Solana sigs are typically 87-88 chars)
function looksLikeSignature(sig) {
  if (typeof sig !== "string") return false;
  const s = sig.trim();
  if (s.length < 80 || s.length > 100) return false;
  // base58 characters (no 0, O, I, l)
  return /^[1-9A-HJ-NP-Za-km-z]+$/.test(s);
}

/**
 * @param {string} txSignature
 * @returns {Promise<string|null>} memo string if found, else null
 */
async function verifyProof(txSignature) {
  const sig = (txSignature || "").trim();

  if (!looksLikeSignature(sig)) {
    console.log("❌ Invalid transaction signature format.");
    console.log("Got:", JSON.stringify(txSignature));
    return null;
  }

  const connection = new Connection(clusterApiUrl("devnet"), "confirmed");

  try {
    const tx = await connection.getParsedTransaction(sig, {
      commitment: "confirmed",
      maxSupportedTransactionVersion: 0,
    });

    if (!tx) {
      console.log("❌ Transaction not found on devnet.");
      return null;
    }

    for (const instruction of tx.transaction.message.instructions) {
      if (
        instruction.programId &&
        instruction.programId.toBase58() === MEMO_PROGRAM_ID.toBase58()
      ) {
        // parsed is usually the memo string for Memo program
        const memo = instruction.parsed;
        console.log("✅ Proof found:");
        console.log(memo);
        return memo || null;
      }
    }

    console.log("❌ No memo found in this transaction.");
    return null;
  } catch (err) {
    console.log("❌ RPC error while fetching transaction.");
    console.log(String(err?.message || err));
    return null;
  }
}

module.exports = verifyProof;