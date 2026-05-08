#!/usr/bin/env swift
import AppKit
import Foundation

let args = Array(CommandLine.arguments.dropFirst())
let language = args.first ?? "es"
let inputPath = args.count > 1 ? args[1] : nil
let outputPath = args.count > 2 ? args[2] : nil
let input: String
if let inputPath {
    input = (try? String(contentsOfFile: inputPath, encoding: .utf8)) ?? ""
} else {
    input = String(data: FileHandle.standardInput.readDataToEndOfFile(), encoding: .utf8) ?? ""
}
let checker = NSSpellChecker.shared
let tag = 0
var outputLines: [String] = []

func emit(_ value: [String: Any]) {
    guard JSONSerialization.isValidJSONObject(value),
          let data = try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]),
          let text = String(data: data, encoding: .utf8) else {
        return
    }
    outputLines.append(text)
}

for rawLine in input.split(whereSeparator: \.isNewline) {
    let token = rawLine.trimmingCharacters(in: .whitespacesAndNewlines)
    if token.isEmpty {
        continue
    }
    let range = checker.checkSpelling(
        of: token,
        startingAt: 0,
        language: language,
        wrap: false,
        inSpellDocumentWithTag: tag,
        wordCount: nil
    )
    if range.location == NSNotFound {
        continue
    }
    let guesses = checker.guesses(
        forWordRange: NSRange(location: 0, length: (token as NSString).length),
        in: token,
        language: language,
        inSpellDocumentWithTag: tag
    ) ?? []
    emit([
        "token": token,
        "language": language,
        "guesses": Array(guesses.prefix(8)),
    ])
}

let output = outputLines.joined(separator: "\n") + (outputLines.isEmpty ? "" : "\n")
if let outputPath {
    try? output.write(toFile: outputPath, atomically: true, encoding: .utf8)
} else {
    print(output, terminator: "")
}
