// Set by first-pages.mjs's firstPagesAboutContent/firstPagesContactFormBlock
// steps for navigation-menus.mjs's steps (which run later in manifest.json
// order in the same invocation) to read back. A single exported mutable
// object, not exported `let` primitives, so both modules see live updates
// without needing getter/setter functions.
export const pageState = {
  aboutPageId: undefined,
  contactPageId: undefined,
};
