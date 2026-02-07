const {
  Connection,
  Keypair,
  clusterApiUrl,
  Transaction,
  sendAndConfirmTransaction,
} = require("@solana/web3.js");

const { createMemoInstruction } = require("@solana/spl-memo");

const fs = require("fs");
const os = require("os");
const path = require("path");
const { execSync } = require("child_process");

// Find wallet path automatically for ANY machine
function resolveKeypairPath() {
  if (process.env.SOLANA_KEYPAIR) return process.env.SOLANA_KEYPAIR;

  try {
    const out = execSync("solana config get", { encoding: "utf8" });
    const line = out.split("\n").find((l) =>
      l.toLowerCase().includes("keypair path")
    );
    if (line) {
      const p = line.split(":").slice(1).join(":").trim();
      if (p) return p;
    }
  } catch {}

  return path.join(os.homedir(), ".config", "solana", "id.json");
}

const keypairPath = resolveKeypairPath();

if (!fs.existsSync(keypairPath)) {
  throw new Error(
    `❌ Could not find Solana keypair. Tried: ${keypairPath}`
  );
}

const secretKey = JSON.parse(fs.readFileSync(keypairPath, "utf8"));
const wallet = Keypair.fromSecretKey(new Uint8Array(secretKey));

/**
 * Stores receipt hash on Solana as memo
 * @param {string} receiptHash
 * @returns {Promise<string>} tx signature
 */
async function certifyProof(receiptHash) {
  if (!receiptHash) throw new Error("receiptHash required");

  const connection = new Connection(clusterApiUrl("devnet"), "confirmed");

  const memoInstruction = createMemoInstruction(
    `DEEPFAKERECEIPT:${receiptHash}`,
    []
  );

  const transaction = new Transaction().add(memoInstruction);

  const signature = await sendAndConfirmTransaction(connection, transaction, [
    wallet,
  ]);

  return signature;
}

module.exports = certifyProof;
