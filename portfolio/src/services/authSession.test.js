import assert from "node:assert/strict";
import test from "node:test";

import { waitForSupabaseSession } from "./authSession.js";

const createAuthStub = ({ immediateSession = null, emitSession = null } = {}) => {
  let listener = null;
  let unsubscribed = false;

  return {
    get unsubscribed() {
      return unsubscribed;
    },
    emit(event, session) {
      listener?.(event, session);
    },
    auth: {
      onAuthStateChange(callback) {
        listener = callback;
        if (emitSession) {
          setTimeout(() => callback("SIGNED_IN", emitSession), 0);
        }
        return {
          data: {
            subscription: {
              unsubscribe() {
                unsubscribed = true;
              },
            },
          },
        };
      },
      async getSession() {
        return { data: { session: immediateSession }, error: null };
      },
    },
  };
};

test("waitForSupabaseSession resolves an already persisted session", async () => {
  const session = { user: { email: "student@sdh.hs.kr" } };
  const stub = createAuthStub({ immediateSession: session });

  const result = await waitForSupabaseSession(stub.auth, { timeoutMs: 50 });

  assert.equal(result, session);
  assert.equal(stub.unsubscribed, true);
});

test("waitForSupabaseSession waits for callback session after an empty initial read", async () => {
  const session = { user: { email: "student@sdh.hs.kr" } };
  const stub = createAuthStub({ emitSession: session });

  const result = await waitForSupabaseSession(stub.auth, { timeoutMs: 50 });

  assert.equal(result, session);
  assert.equal(stub.unsubscribed, true);
});

test("waitForSupabaseSession returns null when no session arrives", async () => {
  const stub = createAuthStub();

  const result = await waitForSupabaseSession(stub.auth, { timeoutMs: 5 });

  assert.equal(result, null);
  assert.equal(stub.unsubscribed, true);
});
