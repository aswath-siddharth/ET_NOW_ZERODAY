import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";
import { encode } from "next-auth/jwt";

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    Credentials({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email", placeholder: "you@example.com" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        try {
          const res = await fetch(`${BACKEND_URL}/api/auth/verify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          if (!res.ok) return null;
          const user = await res.json();
          return { id: user.id, email: user.email, name: user.name };
        } catch {
          return null;
        }
      },
    }),
  ],
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async signIn({ user, account }) {
      // On OAuth sign-in, register the user in our backend
      if (account?.provider === "google" && user.email) {
        try {
          const res = await fetch(`${BACKEND_URL}/api/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: user.email,
              name: user.name,
              provider: "google",
            }),
          });
          if (res.ok) {
            const dbUser = await res.json();
            // Store the DB id so we can use it as the sub claim
            user.id = dbUser.id;
          }
        } catch {
          // Non-blocking — user can still sign in
        }
      }
      return true;
    },
    async jwt({ token, user }) {
      if (user) {
        token.sub = user.id;
        token.email = user.email;
        token.name = user.name;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.sub as string;
      }
      return session;
    },
  },
});

/**
 * Mint a plain HS256 JWT from a NextAuth session for the FastAPI backend.
 * This is called server-side in API routes to forward auth to the backend.
 */
export async function mintBackendToken(session: any): Promise<string | null> {
  if (!session?.user) return null;
  const secret = process.env.AUTH_SECRET;
  if (!secret) return null;

  // Use the jose library to create a simple HS256 JWT
  const { SignJWT } = await import("jose");
  const secretKey = new TextEncoder().encode(secret);
  
  const token = await new SignJWT({
    sub: session.user.id,
    email: session.user.email,
    name: session.user.name,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("1h")
    .sign(secretKey);

  return token;
}
