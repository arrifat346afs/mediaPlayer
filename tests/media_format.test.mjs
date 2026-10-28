// Unit tests for MediaFormat.js. Run with: node --test tests/*.test.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

// The file is a QML JavaScript library; drop the pragma and evaluate it as a script.
const source = readFileSync(new URL("../MediaFormat.js", import.meta.url), "utf8").replace(/^\.pragma library\s*$/m, "");
const MediaFormat = {};
vm.runInNewContext(source, MediaFormat);

test("formatTime pads seconds", () => {
    assert.equal(MediaFormat.formatTime(0), "0:00");
    assert.equal(MediaFormat.formatTime(5), "0:05");
    assert.equal(MediaFormat.formatTime(65), "1:05");
    assert.equal(MediaFormat.formatTime(264), "4:24");
    assert.equal(MediaFormat.formatTime(599.9), "9:59");
});

test("formatTime switches to hours", () => {
    assert.equal(MediaFormat.formatTime(3600), "1:00:00");
    assert.equal(MediaFormat.formatTime(3725), "1:02:05");
    assert.equal(MediaFormat.formatTime(36000 + 59 * 60 + 59), "10:59:59");
});

test("formatTime treats invalid input as zero", () => {
    for (const value of [-1, NaN, Infinity, undefined, null, "abc"])
        assert.equal(MediaFormat.formatTime(value), "0:00", String(value));
});

test("percent clamps and falls back", () => {
    assert.equal(MediaFormat.percent(80, 50), 0.8);
    assert.equal(MediaFormat.percent(0, 50), 0);
    assert.equal(MediaFormat.percent(150, 50), 1);
    assert.equal(MediaFormat.percent(-5, 50), 0);
    assert.equal(MediaFormat.percent("40", 50), 0.4);
    for (const value of [undefined, null, "", "x"])
        assert.equal(MediaFormat.percent(value, 80), 0.8, String(value));
});

test("waveY repeats every width so the strip loops seamlessly", () => {
    const width = 380;
    for (const cycles of [2, 3, 4]) {
        for (const x of [0, 17, 95.5, 200, 379]) {
            const a = MediaFormat.waveY(x, width, 10, 6, cycles, 1.4);
            const b = MediaFormat.waveY(x + width / cycles, width, 10, 6, cycles, 1.4);
            assert.ok(Math.abs(a - b) < 1e-9, `cycles=${cycles} x=${x}`);
        }
    }
});

test("waveY stays within baseline ± amplitude", () => {
    for (let x = 0; x <= 400; x += 7) {
        const y = MediaFormat.waveY(x, 400, 20, 5, 3, 0.3);
        assert.ok(y >= 15 - 1e-9 && y <= 25 + 1e-9);
    }
    assert.equal(MediaFormat.waveY(10, 0, 20, 5, 3, 0), 20);
});
