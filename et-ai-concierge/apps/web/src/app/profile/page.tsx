"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import {
  User, ShieldCheck, FileText, Loader2, Gauge,
} from "lucide-react";

export default function ProfilePage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth");
    } else if (status === "authenticated" && (session as any)?.accessToken) {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
      fetch(`${backendUrl}/api/profile`, {
        headers: {
          Authorization: `Bearer ${(session as any).accessToken}`,
        },
      })
        .then((r) => r.json())
        .then((d) => {
          setProfile(d);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [session, status, router]);

  if (status === "loading" || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const personaDisplay = profile?.persona
    ? profile.persona
        .replace("PERSONA_", "")
        .replace(/_/g, " ")
        .toLowerCase()
        .replace(/\b\w/g, (c: string) => c.toUpperCase())
    : "Unassigned";

  const riskScore = profile?.risk_score ?? 0;
  const riskPercent = (riskScore / 10) * 100;

  return (
    <div className="min-h-screen pt-20 pb-12 px-4 md:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <header className="flex items-center gap-5">
          <div
            className="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center border border-primary/20"
            style={{ boxShadow: "0 0 24px rgba(212,168,83,0.1)" }}
          >
            <User className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              {session?.user?.name || "User"}
            </h1>
            <p className="text-sm text-muted-foreground">{session?.user?.email}</p>
          </div>
        </header>

        <div className="grid md:grid-cols-3 gap-5">
          {/* Profile Data */}
          <div className="md:col-span-2 rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm p-6">
            <h3 className="text-sm font-semibold text-foreground mb-5 flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" />
              Financial Profile
            </h3>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wider">
                  Persona
                </div>
                <div className="font-semibold text-foreground">{personaDisplay}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wider">
                  Risk Score
                </div>
                <div className="flex items-center gap-3">
                  <div className="font-semibold text-foreground font-data">
                    {riskScore || "-"}/10
                  </div>
                  {riskScore > 0 && (
                    <div className="flex-1 h-1.5 rounded-full bg-secondary max-w-[80px] overflow-hidden">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${riskPercent}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wider">
                  Primary Goal
                </div>
                <div className="font-semibold text-foreground capitalize">
                  {profile?.primary_goal || "-"}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wider">
                  Income Type
                </div>
                <div className="font-semibold text-foreground capitalize">
                  {profile?.income_type || "-"}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wider">
                  Age Group
                </div>
                <div className="font-semibold text-foreground capitalize">
                  {profile?.age_group || "-"}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wider">
                  Completeness
                </div>
                <div className="font-semibold text-foreground font-data">
                  {profile?.profile_completeness
                    ? `${Math.round(profile.profile_completeness * 100)}%`
                    : "-"}
                </div>
              </div>
            </div>

            {/* Interests */}
            {profile?.interests && profile.interests.length > 0 && (
              <div className="mt-6 pt-5 border-t border-border/50">
                <div className="text-xs text-muted-foreground mb-2 uppercase tracking-wider">
                  Interests
                </div>
                <div className="flex flex-wrap gap-2">
                  {profile.interests.map((interest: string) => (
                    <span
                      key={interest}
                      className="text-xs bg-primary/10 text-primary px-3 py-1 rounded-full border border-primary/20"
                    >
                      {interest}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Privacy & Audit */}
          <div className="rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm p-6">
            <h3 className="text-sm font-semibold text-foreground mb-5 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Privacy & Audit
            </h3>
            <p className="text-xs text-muted-foreground mb-5 leading-relaxed">
              Your data is encrypted. PII stripping is active before LLM processing.
            </p>
            <div className="space-y-2">
              <button className="w-full py-2.5 rounded-xl border border-border/50 text-sm font-medium text-foreground hover:bg-accent transition">
                View Audit Logs
              </button>
              <button className="w-full py-2.5 rounded-xl border border-border/50 text-sm font-medium text-foreground hover:bg-accent transition">
                Manage Consent
              </button>
              <button className="w-full py-2.5 rounded-xl border border-destructive/30 text-sm font-medium text-destructive hover:bg-destructive/10 transition mt-3">
                Reset Profile
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
