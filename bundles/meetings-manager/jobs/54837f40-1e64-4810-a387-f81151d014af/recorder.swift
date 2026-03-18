import ScreenCaptureKit
import AVFoundation
import CoreMedia
import Foundation

class SystemAudioRecorder: NSObject, SCStreamDelegate, SCStreamOutput {
    var stream: SCStream?
    var audioFile: AVAudioFile?
    var isRecording = false
    let outputURL: URL
    let stopFilePath: String
    var sampleCount: Int = 0

    init(outputPath: String, stopFilePath: String) {
        self.outputURL = URL(fileURLWithPath: outputPath)
        self.stopFilePath = stopFilePath
        super.init()
    }

    func start() async throws {
        try? FileManager.default.removeItem(atPath: stopFilePath)
        try? FileManager.default.removeItem(at: outputURL)

        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: false)
        guard let display = content.displays.first else {
            print("ERROR: No display found")
            exit(1)
        }

        let filter = SCContentFilter(display: display, excludingWindows: [])
        let config = SCStreamConfiguration()
        config.capturesAudio = true
        config.excludesCurrentProcessAudio = true
        config.sampleRate = 16000
        config.channelCount = 1
        config.width = 2
        config.height = 2

        stream = SCStream(filter: filter, configuration: config, delegate: self)
        try stream?.addStreamOutput(self, type: .audio, sampleHandlerQueue: DispatchQueue(label: "audio"))
        try await stream?.startCapture()
        isRecording = true

        print("RECORDING_STARTED")
        print("Output: \(outputURL.path)")
        fflush(stdout)

        while isRecording {
            if FileManager.default.fileExists(atPath: stopFilePath) { break }
            try await Task.sleep(nanoseconds: 500_000_000)
        }

        await stop()
    }

    func stop() async {
        guard isRecording else { return }
        isRecording = false
        try? await stream?.stopCapture()
        // Close the audio file
        audioFile = nil
        try? FileManager.default.removeItem(atPath: stopFilePath)

        let fileSize = (try? FileManager.default.attributesOfItem(atPath: outputURL.path)[.size] as? Int) ?? 0
        print("RECORDING_STOPPED")
        print("Samples captured: \(sampleCount)")
        print("File size: \(fileSize) bytes")
        print("Path: \(outputURL.path)")
        fflush(stdout)
    }

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .audio, isRecording else { return }
        guard sampleBuffer.isValid else { return }
        let numSamples = CMSampleBufferGetNumSamples(sampleBuffer)
        guard numSamples > 0 else { return }

        // Get the audio format from the sample buffer
        guard let formatDesc = CMSampleBufferGetFormatDescription(sampleBuffer),
              let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(formatDesc) else {
            return
        }

        // Create audio file on first sample
        if audioFile == nil {
            let format = AVAudioFormat(streamDescription: asbd)!
            // Write as 16-bit PCM WAV (Whisper-friendly)
            let wavSettings: [String: Any] = [
                AVFormatIDKey: kAudioFormatLinearPCM,
                AVSampleRateKey: asbd.pointee.mSampleRate,
                AVNumberOfChannelsKey: asbd.pointee.mChannelsPerFrame,
                AVLinearPCMBitDepthKey: 16,
                AVLinearPCMIsFloatKey: false,
                AVLinearPCMIsBigEndianKey: false,
                AVLinearPCMIsNonInterleaved: false
            ]
            guard let outputFormat = AVAudioFormat(settings: wavSettings) else {
                print("ERROR: Cannot create output format")
                fflush(stdout)
                return
            }
            do {
                audioFile = try AVAudioFile(forWriting: outputURL, settings: wavSettings)
                print("AUDIO_FILE_CREATED: format=\(format), outputFormat=\(outputFormat)")
                fflush(stdout)
            } catch {
                print("ERROR_CREATING_FILE: \(error)")
                fflush(stdout)
                return
            }
        }

        // Convert CMSampleBuffer to PCMBuffer and write
        guard let blockBuffer = CMSampleBufferGetDataBuffer(sampleBuffer) else { return }
        var length = 0
        var dataPointer: UnsafeMutablePointer<Int8>?
        CMBlockBufferGetDataPointer(blockBuffer, atOffset: 0, lengthAtOffsetOut: nil, totalLengthOut: &length, dataPointerOut: &dataPointer)
        guard let data = dataPointer, length > 0 else { return }

        let format = AVAudioFormat(streamDescription: asbd)!
        let frameCount = AVAudioFrameCount(numSamples)
        guard let pcmBuffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: frameCount) else { return }
        pcmBuffer.frameLength = frameCount

        // Copy data into the PCM buffer
        let bytesPerFrame = Int(asbd.pointee.mBytesPerFrame)
        if bytesPerFrame > 0 && asbd.pointee.mFormatFlags & kAudioFormatFlagIsNonInterleaved != 0 {
            // Non-interleaved float
            if let channelData = pcmBuffer.floatChannelData {
                memcpy(channelData[0], data, min(length, Int(frameCount) * MemoryLayout<Float>.size))
            }
        } else {
            // Interleaved
            if let channelData = pcmBuffer.floatChannelData {
                memcpy(channelData[0], data, min(length, Int(frameCount) * bytesPerFrame))
            }
        }

        do {
            try audioFile?.write(from: pcmBuffer)
            sampleCount += numSamples
        } catch {
            if sampleCount == 0 {
                print("WRITE_ERROR: \(error)")
                fflush(stdout)
            }
        }
    }

    func stream(_ stream: SCStream, didStopWithError error: Error) {
        print("STREAM_ERROR: \(error.localizedDescription)")
        fflush(stdout)
        isRecording = false
    }
}

// --- PERMISSION CHECK ---
func checkPermission() async -> Bool {
    do {
        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: false)
        return !content.displays.isEmpty
    } catch {
        return false
    }
}

// --- MAIN ---
let args = CommandLine.arguments

if args.count >= 2 && args[1] == "--check-permission" {
    Task {
        let granted = await checkPermission()
        print(granted ? "PERMISSION_GRANTED" : "PERMISSION_DENIED")
        fflush(stdout)
        exit(granted ? 0 : 1)
    }
    RunLoop.main.run()
} else {
    guard args.count >= 3 else {
        print("Usage: recorder <output_path> <stop_file_path>")
        print("       recorder --check-permission")
        exit(1)
    }

    let outputPath = args[1]
    let stopFilePath = args[2]
    let recorder = SystemAudioRecorder(outputPath: outputPath, stopFilePath: stopFilePath)

    signal(SIGTERM) { _ in
        FileManager.default.createFile(atPath: CommandLine.arguments[2], contents: nil)
    }
    signal(SIGINT) { _ in
        FileManager.default.createFile(atPath: CommandLine.arguments[2], contents: nil)
    }

    Task {
        let granted = await checkPermission()
        if !granted {
            print("PERMISSION_DENIED")
            fflush(stdout)
            exit(2)
        }
        do {
            try await recorder.start()
        } catch {
            let errStr = "\(error)"
            if errStr.contains("-3801") || errStr.contains("declined TCCs") {
                print("PERMISSION_DENIED")
            } else {
                print("ERROR: \(error)")
            }
            fflush(stdout)
            exit(1)
        }
        exit(0)
    }
    RunLoop.main.run()
}
