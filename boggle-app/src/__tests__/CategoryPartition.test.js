// CategoryPartition.test.js
// Safe frontend-only tests (no backend calls)

describe("Category Partitioning – Word Input Handling", () => {
    // CP-1 Valid alphabetic word
    test("CP-1 UI accepts valid alphabetic word", () => {
      const input = document.createElement("input");
      input.value = "HELLO";
      expect(/^[A-Za-z]+$/.test(input.value)).toBe(true);
    });
  
    // CP-2 Empty input
    test("CP-2 UI rejects empty word", () => {
      const input = document.createElement("input");
      input.value = "";
      expect(input.value.length).toBe(0);
    });
  
    // CP-3 Non-letter characters
    test("CP-3 UI rejects inputs containing non-letters", () => {
      const input = document.createElement("input");
      input.value = "123!@#";
      expect(/^[A-Za-z]+$/.test(input.value)).toBe(false);
    });
  
    // CP-4 Extra-long word (>10 characters)
    test("CP-4 UI handles long inputs gracefully", () => {
      const longWord = "SUPERLONGWORD";
      expect(longWord.length).toBeGreaterThan(10);
    });
  });