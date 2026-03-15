// AudioManager.swift
// CHARLI Glasses - Audio & Wake Word Manager
//
// Handles three things:
//   1. Wake word detection — listens for "Hey Charli" using Porcupine
//   2. Audio recording — captures from Bluetooth mic (glasses)
//   3. Audio playback — plays CHARLI's response through Bluetooth speakers (glasses)
//
// The Meta Ray-Ban glasses appear as a standard Bluetooth audio device.
// When paired to the iPhone, their mic shows up as an audio input source
// and their speakers as an output source. We configure AVAudioSession to
// prefer Bluetooth routes, so audio flows through the glasses automatically.
//
// Wake word detection runs continuously in the background using Porcupine's
// iOS SDK — same library used on the Raspberry Pi desk hub.

import Foundation
import AVFoundation
import Combine

// ── CHARLI State Machine ────────────────────────────────────────────
// Same states as the desk hub: IDLE → LISTENING → THINKING → SPEAKING → IDLE
enum CHARLIState: String {
    case idle      = "idle"
    case listening = "listening"
    case thinking  = "thinking"
    case speaking  = "speaking"

    var displayName: String {
        switch self {
        case .idle:      return "Waiting for \"Hey Charli\"..."
        case .listening: return "Listening..."
        case .thinking:  return "Thinking..."
        case .speaking:  return "Speaking..."
        }
    }
}

// ── Audio Manager ───────────────────────────────────────────────────
class AudioManager: ObservableObject {
    // Published properties update the SwiftUI views automatically
    @Published var state: CHARLIState = .idle
    @Published var glassesConnected: Bool = false

    // Audio session for Bluetooth routing
    private let audioSession = AVAudioSession.sharedInstance()

    // Audio recorder and player
    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?

    // Recording duration (matches desk hub's 5 seconds)
    private let recordingDuration: TimeInterval = 5.0

    // Timer for recording duration
    private var recordingTimer: Timer?

    // URL for the recorded audio file
    private var recordingURL: URL {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        return docs.appendingPathComponent("charli_recording.wav")
    }

    init() {
        setupAudioSession()
        checkBluetoothConnection()
    }

    // ── Audio Session Setup ─────────────────────────────────────
    // Configure iOS audio to route through Bluetooth (glasses) when available.
    private func setupAudioSession() {
        do {
            // .playAndRecord allows simultaneous mic input + speaker output
            // .allowBluetooth enables Bluetooth HFP (headset) profile
            // .defaultToSpeaker falls back to iPhone speaker if no Bluetooth
            try audioSession.setCategory(
                .playAndRecord,
                mode: .default,
                options: [.allowBluetooth, .defaultToSpeaker]
            )
            try audioSession.setActive(true)
            print("✅ Audio session configured for Bluetooth")
        } catch {
            print("❌ Audio session error: \(error)")
        }
    }

    // ── Bluetooth Detection ─────────────────────────────────────
    // Check if the glasses (or any Bluetooth audio device) are connected.
    func checkBluetoothConnection() {
        let currentRoute = audioSession.currentRoute
        let hasBluetooth = currentRoute.outputs.contains { output in
            output.portType == .bluetoothA2DP ||
            output.portType == .bluetoothHFP ||
            output.portType == .bluetoothLE
        }
        DispatchQueue.main.async {
            self.glassesConnected = hasBluetooth
        }
        print(hasBluetooth ? "🕶️ Bluetooth audio connected" : "📱 Using iPhone audio")
    }

    // ── Wake Word Detection ─────────────────────────────────────
    // TODO: Integrate Picovoice Porcupine iOS SDK
    //
    // Porcupine works the same on iOS as on the Pi:
    //   1. Import PorcupineManager from the Picovoice pod
    //   2. Initialize with access key + "Hey Charli" model
    //   3. Call .start() to begin listening
    //   4. Callback fires when wake word detected → start recording
    //
    // Pod: pod 'Porcupine-iOS'
    // SPM: https://github.com/Picovoice/porcupine-ios
    //
    // Example integration:
    //   let porcupine = try PorcupineManager(
    //       accessKey: "<PICOVOICE_ACCESS_KEY>",
    //       keyword: .custom(path: "hey-charli_en_ios.ppn"),
    //       onDetection: { [weak self] in
    //           self?.startRecording()
    //       }
    //   )
    //   porcupine.start()

    func startWakeWordDetection() {
        print("👂 Wake word detection started (TODO: integrate Porcupine)")
        // Placeholder — will be replaced with Porcupine integration
    }

    func stopWakeWordDetection() {
        print("🔇 Wake word detection stopped")
    }

    // ── Manual Trigger ──────────────────────────────────────────
    // For testing: manually start recording without wake word
    func manualTrigger() {
        guard state == .idle else { return }
        startRecording()
    }

    // ── Recording ───────────────────────────────────────────────
    // Record audio from the active mic (glasses Bluetooth or iPhone mic).
    func startRecording() {
        state = .listening

        // Recording settings: 16kHz mono WAV (same as desk hub)
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 16000.0,
            AVNumberOfChannelsKey: 1,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false,
        ]

        do {
            audioRecorder = try AVAudioRecorder(url: recordingURL, settings: settings)
            audioRecorder?.record()

            // Stop recording after 5 seconds (same as desk hub)
            recordingTimer = Timer.scheduledTimer(withTimeInterval: recordingDuration, repeats: false) { [weak self] _ in
                self?.stopRecording()
            }

            print("🎙️ Recording from \(glassesConnected ? "glasses" : "iPhone") mic...")
        } catch {
            print("❌ Recording error: \(error)")
            state = .idle
        }
    }

    func stopRecording() {
        audioRecorder?.stop()
        audioRecorder = nil
        recordingTimer?.invalidate()
        recordingTimer = nil

        state = .thinking
        print("📝 Recording saved to \(recordingURL.lastPathComponent)")

        // Notify that recording is ready to send to CHARLI API
        NotificationCenter.default.post(
            name: .recordingReady,
            object: nil,
            userInfo: ["url": recordingURL]
        )
    }

    // ── Playback ────────────────────────────────────────────────
    // Play CHARLI's audio response through the glasses speakers.
    func playResponse(data: Data) {
        state = .speaking

        do {
            audioPlayer = try AVAudioPlayer(data: data)
            audioPlayer?.delegate = AudioPlayerDelegate { [weak self] in
                // When playback finishes, go back to idle
                DispatchQueue.main.async {
                    self?.state = .idle
                    self?.startWakeWordDetection()
                }
            }
            audioPlayer?.play()
            print("🔊 Playing response through \(glassesConnected ? "glasses" : "iPhone") speakers")
        } catch {
            print("❌ Playback error: \(error)")
            state = .idle
        }
    }
}

// ── Notification for recording ready ────────────────────────────────
extension Notification.Name {
    static let recordingReady = Notification.Name("charli.recordingReady")
}

// ── Audio Player Delegate ───────────────────────────────────────────
// Wraps AVAudioPlayerDelegate in a closure-based API for cleaner code.
class AudioPlayerDelegate: NSObject, AVAudioPlayerDelegate {
    let onFinish: () -> Void

    init(onFinish: @escaping () -> Void) {
        self.onFinish = onFinish
    }

    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        onFinish()
    }
}
