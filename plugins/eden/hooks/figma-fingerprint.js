// Eden design cache — read-only fingerprint of Figma nodes, run through figma_execute (Desktop Bridge).
// eden_design.py `fingerprint-js <node ids…>` prints this file with the ids filled in.
// It walks each node's subtree, serialises the properties that define the design and returns only a
// short hash per node: the whole tree never reaches the model. It never modifies the document.
const IDS = __IDS__;
const KEYS = ['type', 'name', 'visible', 'width', 'height', 'layoutMode', 'layoutWrap',
  'primaryAxisAlignItems', 'counterAxisAlignItems', 'primaryAxisSizingMode', 'counterAxisSizingMode',
  'layoutSizingHorizontal', 'layoutSizingVertical', 'layoutAlign', 'layoutGrow', 'paddingTop',
  'paddingRight', 'paddingBottom', 'paddingLeft', 'itemSpacing', 'counterAxisSpacing', 'minWidth',
  'maxWidth', 'minHeight', 'maxHeight', 'cornerRadius', 'topLeftRadius', 'topRightRadius',
  'bottomLeftRadius', 'bottomRightRadius', 'strokeWeight', 'strokeAlign', 'opacity', 'blendMode',
  'clipsContent', 'characters', 'fontSize', 'fontName', 'fontWeight', 'lineHeight', 'letterSpacing',
  'textCase', 'textDecoration', 'textAlignHorizontal', 'textAlignVertical', 'textAutoResize', 'fills',
  'strokes', 'effects', 'boundVariables', 'fillStyleId', 'textStyleId', 'effectStyleId',
  'componentProperties'];

function hash(s) {
  let h1 = 0x811c9dc5, h2 = 0x01000193 ^ s.length;
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    h1 = Math.imul(h1 ^ c, 16777619) >>> 0;
    h2 = Math.imul(h2 ^ c, 2246822519) >>> 0;
  }
  return h1.toString(16).padStart(8, '0') + h2.toString(16).padStart(8, '0');
}

const nodes = [];
for (const id of IDS) {
  const root = await figma.getNodeByIdAsync(id);
  if (!root) { nodes.push({ id, missing: true }); continue; }
  let count = 0;
  // Built with push + Object.fromEntries: eden_figma_guard.py rejects assignment by index, because on
  // a node it would write to Figma. Key order (and so the hash) is the same as before.
  const snap = (n) => {
    count++;
    const entries = [];
    for (const k of KEYS) {
      let v;
      try { v = n[k]; } catch (e) { continue; }
      if (v === undefined || v === figma.mixed) continue;
      entries.push([k, v]);
    }
    if ('children' in n) entries.push(['c', n.children.map(snap)]);
    return Object.fromEntries(entries);
  };
  const s = JSON.stringify(snap(root));
  nodes.push({ id: root.id, name: root.name, type: root.type, width: Math.round(root.width),
    count, hash: hash(s) });
}
return { fileKey: figma.fileKey, nodes };
