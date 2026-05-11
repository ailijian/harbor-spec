export function foo(a: string): number {
  return a.length;
}

export async function loadFoo(a: string): Promise<number> {
  return a.length;
}

export const makeFoo = (a: string): number => {
  return a.length;
};

export const makeFooAsync = async (a: string): Promise<number> => {
  return a.length;
};

export class UserService {
  public getUser(id: string): User {
    return { id } as User;
  }
}
