// CHARLIAPIClient.swift
// CHARLI Glasses - HTTP Client for CHARLI Server
//
// Handles communication between the iOS app and the central CHARLI Server
// (NestJS on Mac Mini). Sends audio recordings (and optionally images)
// to the server, receives audio responses back.
//
// The server runs on the Mac Mini at port 3000, accessible via Tailscale.
// All requests require an X-API-Key header for device authentication.
//
// Endpoint mapping (old glasses API → new central server):
//   /api/voice-query     → /api/pipeline/voice
//   /api/voice-query-text → /api/pipeline/voice-text
//   /api/ask-vision      → /api/ask/vision
//   /api/ask             → /api/ask
//   /api/conversation    → /api/conversation
//   /health              → /health

import Foundation
import Combine

class CHARLIAPIClient: ObservableObject {
    // Published properties for UI updates
    @Published var isConnected: Bool = false
    @Published var lastQuestion: String?
    @Published var lastResponse: String?

    // Server URL — points to the central CHARLI Server on Mac Mini.
    private let baseURL: String

    // API key for device authentication (registered in charli_server DB).
    private let apiKey: String

    // URL session for HTTP requests
    private let session = URLSession.shared

    // Cancellables for Combine subscriptions
    private var cancellables = Set<AnyCancellable>()

    init() {
        // CHARLI Server URL — Mac Mini on Tailscale (port 3000).
        // Configurable via UserDefaults for testing different servers.
        self.baseURL = UserDefaults.standard.string(forKey: "charli_server_url")
            ?? "http://charli-server:3000"

        // API key for the glasses device (created by charli_server seed/registration).
        self.apiKey = UserDefaults.standard.string(forKey: "charli_api_key")
            ?? ""

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

    // ── Common Headers ────────────────────────────────────────────
    // All API requests include the device API key for authentication.
    private func authHeaders() -> [String: String] {
        return ["X-API-Key": apiKey]
    }

    // ── Health Check ────────────────────────────────────────────
    private func startHealthCheck() {
        Timer.publish(every: 10, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                self?.checkHealth()
            }
            .store(in: &cancellables)

        checkHealth()
    }

    private func checkHealth() {
        guard let url = URL(string: "\(baseURL)/health") else { return }

        // Health endpoint does not require auth
        session.dataTask(with: url) { [weak self] data, response, error in
            let connected = (response as? HTTPURLResponse)?.statusCode == 200
            DispatchQueue.main.async {
                self?.isConnected = connected
            }
        }.resume()
    }

    // ── Voice Query (Full Pipeline) ─────────────────────────────
    // Send recorded audio to CHARLI Server, get audio response back.
    //
    // Endpoint: POST /api/pipeline/voice
    // Input:  multipart form — audio file + optional image file
    // Output: WAV audio response
    // Headers: X-Transcription, X-Language, X-Answer (URL-encoded)

    @objc private func handleRecordingReady(_ notification: Notification) {
        guard let url = notification.userInfo?["url"] as? URL else { return }
        sendVoiceQuery(audioURL: url)
    }

    func sendVoiceQuery(audioURL: URL, imageData: Data? = nil) {
        guard let url = URL(string: "\(baseURL)/api/pipeline/voice") else {
            print("❌ Invalid API URL")
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        // Add auth header
        for (key, value) in authHeaders() {
            request.setValue(value, forHTTPHeaderField: key)
        }

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
                // Extract metadata from response headers
                let transcription = httpResponse.value(forHTTPHeaderField: "X-Transcription")?
                    .removingPercentEncoding ?? ""
                let answer = httpResponse.value(forHTTPHeaderField: "X-Answer")?
                    .removingPercentEncoding ?? ""

                print("✅ Got audio response (\(audioData.count) bytes)")
                print("💬 Heard: \(transcription)")
                print("🤖 CHARLI: \(answer)")

                DispatchQueue.main.async {
                    self?.lastQuestion = transcription
                    self?.lastResponse = answer

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

    // ── Text Query ─────────────────────────────────────────────
    // Send a text question (no audio). Returns text response.
    // Endpoint: POST /api/ask

    func sendTextQuery(question: String) async {
        guard let url = URL(string: "\(baseURL)/api/ask") else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Add auth header
        for (key, value) in authHeaders() {
            request.setValue(value, forHTTPHeaderField: key)
        }

        let body: [String: Any] = ["question": question, "language": "en"]
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

    // ── Vision Query (Text + Image) ─────────────────────────────
    // Send a text question with a base64 image. Returns text response.
    // Endpoint: POST /api/ask/vision
    //
    // Use this when you have the image already as Data (e.g., from camera)
    // and want just the text answer (no audio).

    func sendVisionQuery(question: String, imageData: Data, imageMime: String = "image/jpeg") async {
        guard let url = URL(string: "\(baseURL)/api/ask/vision") else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        for (key, value) in authHeaders() {
            request.setValue(value, forHTTPHeaderField: key)
        }

        let imageBase64 = imageData.base64EncodedString()
        let body: [String: Any] = [
            "question": question,
            "language": "en",
            "imageBase64": imageBase64,
            "imageMime": imageMime,
        ]
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
            print("❌ Vision query error: \(error)")
        }
    }

    // ── Conversation Management ─────────────────────────────────

    func clearConversation() async {
        guard let url = URL(string: "\(baseURL)/api/conversation") else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"

        for (key, value) in authHeaders() {
            request.setValue(value, forHTTPHeaderField: key)
        }

        do {
            let _ = try await session.data(for: request)
            print("✅ Conversation cleared")
        } catch {
            print("❌ Clear conversation error: \(error)")
        }
    }
}

// ── Notification for response audio ─────────────────────────────────
extension Notification.Name {
    static let responseAudioReady = Notification.Name("charli.responseAudioReady")
}

// ── Multipart Form Data Helper ──────────────────────────────────────
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
