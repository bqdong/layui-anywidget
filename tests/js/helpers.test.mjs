// Unit tests for the bridge's pure helpers.
//
// The bridge is an ESM built for the browser; `node --test` can import it as
// long as DOM globals are stubbed, because importing only defines functions.

import assert from "node:assert/strict";
import { test } from "node:test";

// Minimal globals referenced at module scope.
globalThis.window = globalThis;
globalThis.Node = class Node {};

const { __internals } = await import("../../layui_anywidget/static/layui-bridge.js");
const { jsonSafe, isVisible, resolveStateRefs, resolveTheme, optionValue } = __internals;

test("jsonSafe passes JSON primitives through", () => {
  assert.equal(jsonSafe("x"), "x");
  assert.equal(jsonSafe(1.5), 1.5);
  assert.equal(jsonSafe(true), true);
  assert.equal(jsonSafe(null), null);
  assert.equal(jsonSafe(undefined), null);
});

test("jsonSafe nulls non-finite numbers and callables", () => {
  assert.equal(jsonSafe(Number.NaN), null);
  assert.equal(jsonSafe(Infinity), null);
  assert.equal(jsonSafe(() => 1), null);
  assert.equal(jsonSafe(Symbol("s")), null);
});

test("jsonSafe truncates long strings", () => {
  assert.equal(jsonSafe("x".repeat(5000)).length, 4000);
});

test("jsonSafe copies plain objects and arrays", () => {
  assert.deepEqual(jsonSafe({ a: [1, { b: 2 }] }), { a: [1, { b: 2 }] });
});

test("jsonSafe drops DOM nodes and circular references", () => {
  assert.equal(jsonSafe({ nodeType: 1, nodeName: "DIV" }), null);
  const loop = { name: "loop" };
  loop.self = loop;
  assert.deepEqual(jsonSafe(loop), { name: "loop", self: null });
});

test("jsonSafe caps depth and array length", () => {
  let deep = {};
  let cursor = deep;
  for (let i = 0; i < 10; i += 1) {
    cursor.next = {};
    cursor = cursor.next;
  }
  let value = jsonSafe(deep);
  for (let i = 0; i < 4; i += 1) value = value.next;
  assert.equal(value.next, null);

  const wide = jsonSafe(Array.from({ length: 300 }, (_, i) => i));
  assert.equal(wide.length, 200);
});

test("isVisible handles booleans, keys, and comparisons", () => {
  const state = { show: true, mode: "a", count: 2, list: [1, 2] };
  assert.equal(isVisible(undefined, state), true);
  assert.equal(isVisible(true, state), true);
  assert.equal(isVisible(false, state), false);
  assert.equal(isVisible("show", state), true);
  assert.equal(isVisible("missing", state), false);
  assert.equal(isVisible({ key: "mode", equals: "a" }, state), true);
  assert.equal(isVisible({ key: "mode", not_equals: "a" }, state), false);
  assert.equal(isVisible({ key: "count", in: [1, 2] }, state), true);
  assert.equal(isVisible({ key: "count", truthy: false }, state), false);
});

test("resolveStateRefs substitutes $state and $bind", () => {
  const state = { rows: [1], name: "Ada" };
  assert.deepEqual(resolveStateRefs({ $state: "rows" }, state), [1]);
  assert.deepEqual(resolveStateRefs({ $bind: "name" }, state), "Ada");
  assert.deepEqual(
    resolveStateRefs({ data: { $state: "rows" }, title: "x" }, state),
    { data: [1], title: "x" },
  );
  assert.deepEqual(resolveStateRefs([{ $state: "name" }], state), ["Ada"]);
  assert.equal(resolveStateRefs("plain", state), "plain");
});

test("resolveTheme honours explicit preferences", () => {
  assert.equal(resolveTheme("dark"), "dark");
  assert.equal(resolveTheme("light"), "light");
  assert.ok(["dark", "light"].includes(resolveTheme("auto")));
});

test("optionValue normalizes scalars and mappings", () => {
  assert.deepEqual(optionValue("x"), { label: "x", value: "x", disabled: false });
  assert.deepEqual(optionValue({ label: "A", value: 1, disabled: true }), {
    label: "A",
    value: 1,
    disabled: true,
  });
  assert.deepEqual(optionValue({ text: "T", value: 2 }), {
    label: "T",
    value: 2,
    disabled: false,
  });
});
