"use client";

import { useState, useEffect } from "react";
import { User, Settings, ShieldCheck, FileText } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function ProfilePage() {
  const [profile, setProfile] = useState<any>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/profile/test_user_123")
      .then(r => r.json())
      .then(d => setProfile(d))
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="flex items-center gap-6">
          <div className="w-20 h-20 rounded-full bg-primary/20 text-primary flex items-center justify-center border-4 border-background shadow-xl">
            <User className="w-10 h-10" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Your Financial Profile</h1>
            <p className="text-muted-foreground mt-1">ID: test_user_123</p>
          </div>
        </header>

        <div className="grid md:grid-cols-3 gap-6">
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" /> Profile Data
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Assigned Persona</div>
                  <div className="font-semibold text-lg">{profile?.persona || "Unassigned"}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Risk Score (1-10)</div>
                  <div className="font-semibold text-lg">{profile?.risk_score || "-"}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Primary Goal</div>
                  <div className="font-semibold text-lg capitalize">{profile?.primary_goal || "-"}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Income Type</div>
                  <div className="font-semibold text-lg capitalize">{profile?.income_type || "-"}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-500" /> Privacy & Audit
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Your data is encrypted. PII stripping is active before LLM processing.
              </p>
              <Button variant="outline" className="w-full">View Audit Logs</Button>
              <Button variant="outline" className="w-full">Manage Consent</Button>
              <Button variant="destructive" className="w-full mt-4 bg-destructive/20 text-destructive hover:bg-destructive hover:text-white border-transparent">
                Reset Profile
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
