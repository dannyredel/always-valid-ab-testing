// Hash assignment, port of ablab/assign.py: MurmurHash3 x86_32 of the UTF-8 bytes of
// "player_id:experiment_key", seed 0, scaled to [0, 1). Must match fixtures/assign.json exactly.

const encoder = new TextEncoder();

export function murmur3_32(bytes: Uint8Array, seed = 0): number {
  const c1 = 0xcc9e2d51;
  const c2 = 0x1b873593;
  const n = bytes.length;
  const nBlocks = n >>> 2;
  let h = seed >>> 0;

  for (let i = 0; i < nBlocks; i++) {
    const j = i * 4;
    let k = (bytes[j]! | (bytes[j + 1]! << 8) | (bytes[j + 2]! << 16) | (bytes[j + 3]! << 24)) >>> 0;
    k = Math.imul(k, c1);
    k = (k << 15) | (k >>> 17);
    k = Math.imul(k, c2);
    h ^= k;
    h = (h << 13) | (h >>> 19);
    h = (Math.imul(h, 5) + 0xe6546b64) | 0;
  }

  const tail = nBlocks * 4;
  let k = 0;
  switch (n & 3) {
    case 3:
      k ^= bytes[tail + 2]! << 16;
    // falls through
    case 2:
      k ^= bytes[tail + 1]! << 8;
    // falls through
    case 1:
      k ^= bytes[tail]!;
      k = Math.imul(k, c1);
      k = (k << 15) | (k >>> 17);
      k = Math.imul(k, c2);
      h ^= k;
  }

  h ^= n;
  h ^= h >>> 16;
  h = Math.imul(h, 0x85ebca6b);
  h ^= h >>> 13;
  h = Math.imul(h, 0xc2b2ae35);
  h ^= h >>> 16;
  return h >>> 0;
}

export function assignmentU(playerId: string, key: string): number {
  return murmur3_32(encoder.encode(`${playerId}:${key}`)) / 2 ** 32;
}

/** Below the treatment share means Starter Bonus. */
export function isTreated(u: number, share = 0.5): boolean {
  return u < share;
}
