// ContentView.swift
// CHARLI Glasses - Main UI
//
// Minimal UI for the companion app. Most interaction happens through
// voice (via the glasses), but the app shows status and allows manual
// triggering for testing.
//
// The UI has three main states:
//   - Idle:      Waiting for "Hey Charli" wake word
//   - Listening: Recording audio from glasses mic
//   - Thinking:  Waiting for CHARLI's response
//   - Speaking:  Playing response through glasses speakers

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var audioManager: AudioManager
    @EnvironmentObject var charliAPI: CHARLIAPIClient

    var body: some View {
        NavigationStack {
            VStack(spacing: 30) {

                // ── Status Orb ──────────────────────────────────
                // Visual indicator of CHARLI's current state.
                // Matches the JARVIS UI orb on the desk hub.
                Circle()
                    .fill(orbColor)
                    .frame(width: 120, height: 120)
                    .shadow(color: orbColor.opacity(0.6), radius: 20)
                    .animation(.easeInOut(duration: 0.5), value: audioManager.state)

                Text(audioManager.state.displayName)
                    .font(.title2)
                    .foregroundColor(.secondary)

                // ── Connection Status ───────────────────────────
                HStack(spacing: 16) {
                    StatusBadge(
                        label: "Glasses",
                        connected: audioManager.glassesConnected
                    )
                    StatusBadge(
                        label: "CHARLI API",
                        connected: charliAPI.isConnected
                    )
                }

                // ── Last Response ───────────────────────────────
                if let lastResponse = charliAPI.lastResponse {
                    VStack(alignment: .leading, spacing: 8) {
                        if let question = charliAPI.lastQuestion {
                            Text("You: \(question)")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                        Text("CHARLI: \(lastResponse)")
                            .font(.body)
                            .padding()
                            .background(Color(.systemGray6))
                            .cornerRadius(12)
                    }
                    .padding(.horizontal)
                }

                Spacer()

                // ── Manual Trigger Button ───────────────────────
                // For testing without wake word. Tap to start recording.
                Button(action: {
                    audioManager.manualTrigger()
                }) {
                    Image(systemName: "mic.fill")
                        .font(.system(size: 32))
                        .foregroundColor(.white)
                        .frame(width: 72, height: 72)
                        .background(audioManager.state == .idle ? Color.blue : Color.gray)
                        .clipShape(Circle())
                }
                .disabled(audioManager.state != .idle)

                Text("Tap to talk (or say \"Hey Charli\")")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding()
            .navigationTitle("CHARLI Glasses")
        }
    }

    // Map CHARLI state to orb color (matches desk hub JARVIS UI)
    private var orbColor: Color {
        switch audioManager.state {
        case .idle:      return .blue
        case .listening: return .cyan
        case .thinking:  return .orange
        case .speaking:  return Color(.systemYellow)
        }
    }
}

// ── Status Badge Component ──────────────────────────────────────────
struct StatusBadge: View {
    let label: String
    let connected: Bool

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(connected ? Color.green : Color.red)
                .frame(width: 8, height: 8)
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color(.systemGray6))
        .cornerRadius(20)
    }
}

#Preview {
    ContentView()
        .environmentObject(AudioManager())
        .environmentObject(CHARLIAPIClient())
}
