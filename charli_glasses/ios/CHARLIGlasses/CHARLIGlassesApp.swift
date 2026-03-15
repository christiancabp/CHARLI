// CHARLIGlassesApp.swift
// CHARLI Glasses - iOS Companion App
//
// This app bridges Meta Ray-Ban smart glasses to CHARLI's brain.
// It runs on the iPhone, connecting to the glasses via Bluetooth
// and to CHARLI's API server via WiFi/Tailscale.
//
// The flow:
//   Glasses mic → iPhone (this app) → CHARLI API → iPhone → Glasses speakers
//
// Think of it as a relay station: the glasses are the ears and mouth,
// the iPhone is the messenger, and CHARLI's brain is on the Mac Mini.

import SwiftUI

@main
struct CHARLIGlassesApp: App {
    // The audio manager handles Bluetooth mic/speaker + wake word detection.
    // @StateObject means SwiftUI owns this object's lifecycle —
    // it's created once and shared across all views.
    @StateObject private var audioManager = AudioManager()
    @StateObject private var charliAPI = CHARLIAPIClient()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(audioManager)
                .environmentObject(charliAPI)
        }
    }
}
