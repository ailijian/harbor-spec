/**
 * Calculate score.
 * @param value input value
 * @returns score
 * @throws Error on invalid value
 * @harbor.scope public
 */
export function documentedHigh(value: string): number {
  return value.length;
}

/**
 * Plain description only.
 */
export function documentedMedium(text: string): number {
  return text.length;
}

// @param not a block contract
export function lineCommentOnly(name: string): number {
  return name.length;
}

export function missingDoc(value: string): number {
  return value.length;
}

function internalHelper(input: string): number {
  return input.length;
}

/**
 * This comment should not attach because code exists below.
 */
const gap = 1;
export function separatedDoc(value: string): number {
  return value.length + gap;
}

export class ContractService {
  /**
   * Resolve user data.
   * @param id user id
   * @returns user payload
   */
  public getUser(id: string): User {
    return { id } as User;
  }
}
