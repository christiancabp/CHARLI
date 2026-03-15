// CHARLIAPIClient.swift
// CHARLI Glasses - HTTP Client for CHARLI API
//
// Handles communication between the iOS app and the CHARLI Glasses API
// server. Sends audio recordings (and optionally images) to the server,
// receives audio responses back.
//
// The server can run on:
//   - The Raspberry Pi (http://charli-home.local:8090)
//   - The Mac Mini directly (http://<tailscale-ip>:8090)
//
// All requests go through the Tailscale private network for security.

import Foundation
import Combine

class CHARLIAPIClient: ObservableObject {
    // Published properties for UI updates
    @Published var isConnected: Bool = false
    @Published var lastQuestion: String?
    @Published var lastResponse: String?

    // Server URL — configurable via Settings or hardcoded for now.
    // This points to wherever the CHARLI Glasses API server is running.
    private let baseURL: String

    // URL session for HTTP requests
    private let session = URLSession.shared

    // Cancellables for Combine subscriptions
    private var cancellables = Set<AnyCancellable>()

    init() {
        // Default to the Raspberry Pi's address on Tailscale.
        // In production, this would come from UserDefaults/Settings.
        self.baseURL = UserDefaults.standard.string(forKey: "charli_api_url")
            ?? "http://charli-home.local:8090"

        // Start health check polling
        startHealthCheck()

        // Listen for recording-ready notifications from AudioManager
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleRecordingReady(_:)),
            name: .recordingReady,
            object: nil
        )
    }

    // ── Health Check ────────────────────────────────────────────
    // Poll the server every 10 seconds to check if it's alive.
    private func startHealthCheck() {
        Timer.publish(every: 10, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                self?.checkHealth()
            }
            .store(in: &cancellables)

        // Also check immediately
        checkHealth()
    }

    private func checkHealth() {
        guard let url = URL(string: "\(baseURL)/health") else { return }

        session.dataTask(with: url) { [weak self] data, response, error in
            let connected = (response as? HTTPURLResponse)?.statusCode == 200
            DispatchQueue.main.async {
                self?.isConnected = connected
            }
        }.resume()
    }

    // ── Voice Query (Full Pipeline) ─────────────────────────────
    // Send recorded audio to CHARLI, get audio response back.
    //
    // This is the main function called after recording finishes:
    //   1. Read the WAV file from disk
    //   2. POST to /api/voice-query as multipart form data
    //   3. Receive WAV audio response
    //   4. Pass audio data to AudioManager for playback

    @objc private func handleRecordingReady(_ notification: Notification) {
        guard let url = notification.userInfo?["url"] as? URL else { return }
        sendVoiceQuery(audioURL: url)
    }

    func sendVoiceQuery(audioURL: URL, imageData: Data? = nil) {
        guard let url = URL(string: "\(baseURL)/api/voice-query") else {
            print("❌ Invalid API URL")
            return
        }

        // Build multipart form data request
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        // Add audio file
        if let audioData = try? Data(contentsOf: audioURL) {
            body.appendMultipart(
                boundary: boundary,
                name: "audio",
                filename: "recording.wav",
                contentType: "audio/wav",
                data: audioData
            )
        }

        // Add image if provided (for vision queries)
        if let imageData = imageData {
            body.appendMultipart(
                boundary: boundary,
                name: "image",
                filename: "capture.jpg",
                contentType: "image/jpeg",
                data: imageData
            )
        }

        // Close the multipart body
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        // Send the request
        session.dataTask(with: request) { [weak self] data, response, error in
            if let error = error {
                print("❌ API error: \(error.localizedDescription)")
                return
            }

            guard let httpResponse = response as? HTTPURLResponse else { return }

            if httpResponse.statusCode == 200, let audioData = data {
                // Success — play the audio response through glasses speakers
                print("✅ Got audio response (\(audioData.count) bytes)")
                DispatchQueue.main.async {
                    // Post notification for AudioManager to play
                    NotificationCenter.default.post(
                        name: .responseAudioReady,
                        object: nil,
                        userInfo: ["data": audioData]
                    )
                }
            } else {
                print("❌ API returned status \(httpResponse.statusCode)")
            }
        }.resume()
    }

    // ── Text Query (for testing) ────────────────────────────────
    // Send a text question directly (bypasses audio recording).
    func sendTextQuery(question: String) async {
        guard let url = URL(string: "\(baseURL)/api/ask") else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["question": question, "language": "en"]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        do {
            let (data, _) = try await session.data(for: request)
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let answer = json["answer"] as? String {
                DispatchQueue.main.async {
                    self.lastQuestion = question
                    self.lastResponse = answer
                }
            }
        } catch {
            print("❌ Text query error: \(error)")
        }
    }
}

// ── Notification for response audio ─────────────────────────────────
extension Notification.Name {
    static let responseAudioReady = Notification.Name("charli.responseAudioReady")
}

// ── Multipart Form Data Helper ──────────────────────────────────────
// Builds multipart/form-data body for file uploads.
// This is the Swift equivalent of FormData in JavaScript:
//   const form = new FormData();
//   form.append('audio', audioBlob, 'recording.wav');
extension Data {
    mutating func appendMultipart(
        boundary: String,
        name: String,
        filename: String,
        contentType: String,
        data: Data
    ) {
        let header = [
            "--\(boundary)\r\n",
            "Content-Disposition: form-data; name=\"\(name)\"; filename=\"\(filename)\"\r\n",
            "Content-Type: \(contentType)\r\n\r\n",
        ].joined()

        self.append(header.data(using: .utf8)!)
        self.append(data)
        self.append("\r\n".data(using: .utf8)!)
    }
}
