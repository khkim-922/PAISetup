/* 검사가 먹일 파일을 **굽는다** — 바이너리 검체를 폴더에 두지 않는다.
 *
 * 좌표 — 아뜰리에 #93(봉투 머리) · #146(부르는 화면 검사) · 아뜰리에 결정 0191(못 싣는
 * 그림) · 씨앗 규율은 claude-config 결정 0040.
 *
 * 두면 무엇이 왜 들었는지 아무도 못 열어 보고, 「이 판정의 근거가 이 바이트다」가
 * 말로만 남는다. 여기 있는 것은 전부 **몇 줄로 지어지는 최소 꼴**이라, 무엇을 재려고
 * 무엇을 넣었나가 코드에 그대로 보인다.
 *
 * ⚠ **원본은 실물 규격이다** — 여기 지은 것이 안 열리면 지은 쪽이 틀린 것이지 읽개가
 *   틀린 것이 아니다. 규격을 바꾸지 말고 이 파일을 고친다.
 *
 * ⚠ **새 검사는 여기서 import 하지 사본을 뜨지 않는다** — 이 폴더의 부품 규율이다.
 *
 * ⚠ **앱의 값을 이 파일에 옮겨 적지 않는다 — 그래서 `drmFile` 이 머리를 인자로 받는다.**
 *   옮겨 적으면 봉투 규격이 갈릴 때 검사만 옛 머리를 물고 초록을 낸다. 그 규율은 여기서
 *   **사라진 것이 아니라 자리를 옮겼다**: 진본의 좌표(어느 파일 · 어느 이름)는 그 저장소만
 *   알므로 **부르는 쪽**이 들고, 그 값을 **원문에서 읽어 내는 손**은 여기 `pyBytesLiteral`
 *   이 든다. 부르는 쪽이 바이트를 손으로 쳐 넣으면 그 순간 규율이 깨지는데, 깨진 것을
 *   여기서는 못 본다 — **부르는 검사가 제 진본에서 읽어 넘기는 꼴이어야 원칙이 산다.**
 *
 * ⚠ **`zlib.crc32` 가 없는 판에서는 굽기가 안 선다** — PNG 도 zip 도 CRC 를 물어서다.
 *   자검이 그 자리를 「못 쟀다」(2)로 먼저 말한다. 없으면 침묵이 아니라 `TypeError` 다.
 */
import zlib from "node:zlib";

/** 시험 PNG — 회색 줄무늬 한 장. 폭 판정(원본 크기를 실물에서 재나)의 재료다. */
export function testPng(W = 300, H = 200) {
  const rows = Buffer.concat(Array.from({ length: H }, (_, y) =>
    Buffer.concat([Buffer.from([0]), Buffer.alloc(W, (y * 7) % 256)])));
  const chunk = (type, data) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const body = Buffer.concat([Buffer.from(type, "latin1"), data]);
    const crc = Buffer.alloc(4); crc.writeUInt32BE(zlib.crc32(body) >>> 0);
    return Buffer.concat([len, body, crc]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(H, 4);
  ihdr[8] = 8;                       // 8비트 · 회색조(컬러타입 0) · 필터 없음
  return Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
                        chunk("IHDR", ihdr),
                        chunk("IDAT", zlib.deflateSync(rows)),
                        chunk("IEND", Buffer.alloc(0))]);
}

/** 못 싣는 그림 한 장 — EMF. 판별은 **머리 바이트**다: 0..4 가 `01 00 00 00`,
 *  40..44 가 ` EMF`. 그림으로서 유효할 필요는 없다 — 재는 것은 「이 형식을 화면이
 *  어떻게 다루나」지 그림 내용이 아니다. */
export function testEmf() {
  const b = Buffer.alloc(88);
  b.writeUInt32LE(1, 0);                 // iType = EMR_HEADER
  b.write(" EMF", 40, "latin1");         // 서명
  return b;
}

// --- 최소 zip — 저장(stored) 방식만. docx 를 짓는 데 필요한 만큼이다.
function zipStore(entries) {
  const locals = [], central = [];
  let offset = 0;
  for (const [name, body] of entries) {
    const n = Buffer.from(name, "utf8");
    const crc = zlib.crc32(body) >>> 0;
    const lh = Buffer.alloc(30);
    lh.writeUInt32LE(0x04034b50, 0); lh.writeUInt16LE(20, 4);
    lh.writeUInt16LE(0, 6); lh.writeUInt16LE(0, 8);      // 플래그 없음 · 저장
    lh.writeUInt32LE(crc, 14);
    lh.writeUInt32LE(body.length, 18); lh.writeUInt32LE(body.length, 22);
    lh.writeUInt16LE(n.length, 26); lh.writeUInt16LE(0, 28);
    locals.push(lh, n, body);
    const ch = Buffer.alloc(46);
    ch.writeUInt32LE(0x02014b50, 0); ch.writeUInt16LE(20, 4); ch.writeUInt16LE(20, 6);
    ch.writeUInt32LE(crc, 16);
    ch.writeUInt32LE(body.length, 20); ch.writeUInt32LE(body.length, 24);
    ch.writeUInt16LE(n.length, 28); ch.writeUInt32LE(offset, 42);
    central.push(ch, n);
    offset += 30 + n.length + body.length;
  }
  const dir = Buffer.concat(central);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(entries.length, 8); end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(dir.length, 12); end.writeUInt32LE(offset, 16);
  return Buffer.concat([...locals, dir, end]);
}

const NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
const NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main";
// ⚠ 그림 이름칸은 `main` 아래가 아니다 — `…/drawingml/2006/picture` 다.
//   `NS_A + "/picture"` 로 지으면 읽개가 구조는 알아보고도 그림을 못 잇는다(실측).
const NS_PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture";
const NS_WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing";
const NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
const NS_P = "http://schemas.openxmlformats.org/package/2006/relationships";

/** 워드 한 장 — 문단 하나와 그림 여럿. `figs` 는 [{ name, data }] 순서대로 선다.
 *
 * 읽개는 본문(`word/document.xml`)과 그 rels 위에 곁 파트도 연다 — 번호 매기기·스타일·
 * 각주·차트. 이 검체는 **본문 한 벌**만 지으므로 **그림 한 장이 서는 최소 꼴**이고,
 * 곁 파트가 있어야 서는 것(목록 표식 · 차트 밑자료)은 여기서 안 난다. */
export function testDocx(figs, line = "첫 문단입니다") {
  // ⚠ **맨몸 `a:blip` 으로는 안 된다.** 규격대로 `w:drawing` 안에 `wp:inline` →
  //   `a:graphic` → `pic:pic` 이 서야 그림으로 친다. 안 그러면 **글자는 오는데 그림이
  //   0장**으로 조용히 빠진다(실측). 규격을 아무 데서나 주운 `a:blip` 으로 줄이지 않는다.
  const body = figs.map((f, i) =>
    `<w:p><w:r><w:drawing><wp:inline>`
    + `<wp:extent cx="2857500" cy="1905000"/>`
    + `<wp:docPr id="${i + 1}" name="${f.name}"/>`
    + `<a:graphic><a:graphicData uri="${NS_PIC}"><pic:pic>`
    + `<pic:nvPicPr><pic:cNvPr id="${i + 1}" name="${f.name}"/><pic:cNvPicPr/></pic:nvPicPr>`
    + `<pic:blipFill><a:blip r:embed="rId${i + 1}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>`
    + `<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="2857500" cy="1905000"/></a:xfrm>`
    + `<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>`
    + `</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>`).join("");
  const doc = `<?xml version="1.0" encoding="UTF-8"?>`
    + `<w:document xmlns:w="${NS_W}" xmlns:a="${NS_A}" xmlns:r="${NS_R}"`
    + ` xmlns:wp="${NS_WP}"`
    + ` xmlns:pic="${NS_PIC}"><w:body>`
    + `<w:p><w:r><w:t>${line}</w:t></w:r></w:p>${body}</w:body></w:document>`;
  const rels = `<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="${NS_P}">`
    + figs.map((f, i) => `<Relationship Id="rId${i + 1}" Target="media/${f.name}"`
        + ` Type="${NS_R}/image"/>`).join("") + `</Relationships>`;
  const types = `<?xml version="1.0" encoding="UTF-8"?><Types xmlns="`
    + `http://schemas.openxmlformats.org/package/2006/content-types">`
    + `<Default Extension="xml" ContentType="application/xml"/>`
    + `<Default Extension="png" ContentType="image/png"/>`
    + `<Default Extension="emf" ContentType="image/x-emf"/></Types>`;
  const root = `<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="${NS_P}">`
    + `<Relationship Id="rIdDoc" Target="word/document.xml" Type="${NS_R}/officeDocument"/>`
    + `</Relationships>`;
  const u = s => Buffer.from(s, "utf8");
  return zipStore([
    ["[Content_Types].xml", u(types)],
    ["_rels/.rels", u(root)],
    ["word/document.xml", u(doc)],
    ["word/_rels/document.xml.rels", u(rels)],
    ...figs.map(f => [`word/media/${f.name}`, f.data]),
  ]);
}

/** 파이썬 원문에서 `<이름> = b"…"` 한 줄을 읽어 바이트로 푼다 — **옮겨 적기를 막는 손**.
 *
 * 앱의 값을 검사가 쓸 때 부르는 자리다: 읽을 파일과 이름은 그 저장소가 알고, 원문을
 * 바이트로 바꾸는 일은 여기가 든다. 부르는 쪽은 `readFileSync(…, "latin1")` 로 읽은
 * 글자를 그대로 넘긴다 — `latin1` 이라야 한 바이트가 한 글자로 선다.
 *
 * ⚠ **`\xNN` 말고 다른 이스케이프는 안 푼다** — `\n`·`\t`·`\\` 가 든 값을 조용히 틀린
 *   바이트로 내주는 대신 **그 자리에서 선다.** 그런 값을 넘겨야 하면 이 손을 넓히지,
 *   부르는 쪽에서 바이트를 쳐 넣지 않는다.
 */
export function pyBytesLiteral(source, name) {
  if (!/^[A-Za-z_]\w*$/.test(name)) throw new Error(`이름이 식별자가 아니다: ${name}`);
  const lit = source.match(new RegExp(`^${name} = b"(.*)"$`, "m"))?.[1];
  if (lit === undefined) throw new Error(`원문에서 ${name} 을 못 읽었다 — 모양이 갈렸다`);
  const odd = lit.replace(/\\x[0-9a-fA-F]{2}/g, "").match(/\\./);
  if (odd) throw new Error(`${name} 에 안 푸는 이스케이프가 있다: ${odd[0]}`);
  return Buffer.from(lit.replace(/\\x([0-9a-fA-F]{2})/g,
    (_, h) => String.fromCharCode(parseInt(h, 16))), "latin1");
}

/** 못 여는 봉투 한 장 — **머리 바이트만 진짜**고 속은 아무 덩이나.
 *
 * `head` 는 부르는 쪽이 제 앱의 진본에서 읽어 넘긴다(위 `pyBytesLiteral` · 머리말 ⚠).
 * 돌려주는 `head` 는 넘어온 바로 그 바이트라, 부르는 검사가 「무엇으로 쟀나」를 찍을 수
 * 있다. */
export function drmFile(head) {
  if (!Buffer.isBuffer(head) || head.length === 0)
    throw new Error("머리 바이트를 안 받았다 — 부르는 쪽이 제 진본에서 읽어 넘긴다");
  return { head, file: Buffer.concat([head, Buffer.from("암호 덩이".repeat(40), "utf8")]) };
}

// ── 자검 — `node _check/_bake.mjs --self`. 부품이라 평소엔 아무 판정도 안 낸다.
//    굽는 넷이 **실제로 그 꼴의 바이트를 내나**만 본다. 종료코드 0/1/2 계약.
if (process.argv.includes("--self")) {
  const EXIT_OK = 0, EXIT_MISMATCH = 1, EXIT_UNMEASURED = 2;

  if (typeof zlib.crc32 !== "function") {
    console.log("[안 잼] 이 노드 판에 `zlib.crc32` 가 없다 — 굽기 자체가 안 선다");
    process.exit(EXIT_UNMEASURED);
  }

  const results = [];
  const check = (name, ok, got) => {
    results.push(ok);
    console.log(`  ${ok ? "✅" : "❌"} ${name}${ok ? "" : `\n       실제: ${got}`}`);
  };
  const u32be = (b, at) => b.readUInt32BE(at);

  console.log("1. PNG — 서명과 IHDR 가 준 크기를 되읽힌다");
  {
    const png = testPng(300, 200);
    const sig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
    check("서명 여덟 바이트가 맞다", png.subarray(0, 8).equals(sig),
          png.subarray(0, 8).toString("hex"));
    check("첫 덩이가 IHDR 다", png.subarray(12, 16).toString("latin1") === "IHDR",
          png.subarray(12, 16).toString("latin1"));
    check("폭·높이가 준 값이다 (300×200)",
          u32be(png, 16) === 300 && u32be(png, 20) === 200,
          `${u32be(png, 16)}×${u32be(png, 20)}`);
    // 양성 대조 — 상수를 박아 둔 것이 아니라 인자를 쓰는지. 안 보면 위 줄은 늘 초록이다.
    const other = testPng(64, 48);
    check("   대조: 다른 크기를 주면 되읽은 값도 따라 바뀐다",
          u32be(other, 16) === 64 && u32be(other, 20) === 48,
          `${u32be(other, 16)}×${u32be(other, 20)}`);
  }

  console.log("\n2. EMF — 판별이 무는 머리 두 자리");
  {
    const emf = testEmf();
    check("0..4 가 `01 00 00 00`", emf.readUInt32LE(0) === 1, emf.readUInt32LE(0));
    check("40..44 가 ` EMF`", emf.subarray(40, 44).toString("latin1") === " EMF",
          JSON.stringify(emf.subarray(40, 44).toString("latin1")));
  }

  console.log("\n3. docx — zip 봉투로 서고 넣은 그림이 파트로 선다");
  {
    const figs = [{ name: "image1.png", data: testPng() },
                  { name: "image2.emf", data: testEmf() }];
    const docx = testDocx(figs);
    check("zip 지역 머리(`PK\\x03\\x04`)로 연다",
          docx.readUInt32LE(0) === 0x04034b50, docx.subarray(0, 4).toString("hex"));
    check("끝에 중앙 디렉터리 꼬리(`PK\\x05\\x06`)가 있다",
          docx.readUInt32LE(docx.length - 22) === 0x06054b50,
          docx.subarray(docx.length - 22, docx.length - 18).toString("hex"));
    // 센티널 — 파트 수를 손으로 안 적는다. 고정 넷 + 그림 수가 꼬리에 그대로 서야 한다.
    const want = 4 + figs.length;
    check(`파트 수가 고정 넷 + 그림 ${figs.length} 이다`,
          docx.readUInt16LE(docx.length - 22 + 10) === want,
          docx.readUInt16LE(docx.length - 22 + 10));
    const text = docx.toString("latin1");
    check("넣은 그림 이름이 다 파트로 선다",
          figs.every(f => text.includes(`word/media/${f.name}`)),
          figs.filter(f => !text.includes(`word/media/${f.name}`)).map(f => f.name).join("·"));
    check("그림이 `pic:pic` 안에 선다 — 맨몸 `a:blip` 이 아니다",
          text.includes("<pic:pic>") && text.includes(`uri="${NS_PIC}"`),
          text.includes("<pic:pic>"));
  }

  console.log("\n4. 원문에서 읽은 머리로 봉투가 선다 — 옮겨 적기를 안 거친다");
  {
    const SRC = 'X = 1\nHEAD = b"\\x9b ABC"\nY = 2\n';
    const head = pyBytesLiteral(SRC, "HEAD");
    check("`\\xNN` 이 바이트로 풀린다",
          head.equals(Buffer.from([0x9b, 0x20, 0x41, 0x42, 0x43])), head.toString("hex"));
    const bad = (fn) => { try { fn(); return null; } catch (e) { return e.message; } };
    // 양성 대조 셋 — 「없다」가 조용한 빈 값이 아니라 선 자리로 나오나.
    check("   대조: 없는 이름은 선다", bad(() => pyBytesLiteral(SRC, "NOPE")) !== null, "안 섰다");
    check("   대조: 안 푸는 이스케이프는 선다",
          bad(() => pyBytesLiteral('H = b"a\\nb"\n', "H")) !== null, "안 섰다");
    check("   대조: 머리를 안 넘기면 선다", bad(() => drmFile()) !== null, "안 섰다");

    const { head: back, file } = drmFile(head);
    check("봉투가 그 머리로 시작한다", file.subarray(0, head.length).equals(head),
          file.subarray(0, head.length).toString("hex"));
    check("돌려준 머리가 넘긴 바로 그 바이트다", back === head, "다른 것이 왔다");
    check("머리 뒤에 속이 붙는다", file.length > head.length, file.length);
  }

  console.log("\n경계 — 이 자검이 **안 재는** 것");
  for (const row of [
    "실물 읽개가 이것을 여나 — 그건 이 부품을 먹이는 검사의 몫이지 굽는 자의 몫이 아니다.",
    "실물 봉투는 못 쓴다 — 머리 바이트만 진짜고 속은 아무 덩이다.",
    "PNG 픽셀 내용·EMF 레코드 본문의 유효성 — 재는 것은 머리와 크기지 그림이 아니다.",
    "zip 의 다른 압축 방식 — 저장(stored) 하나만 짓는다.",
    "곁 파트(번호 매기기·스타일·각주·차트)가 있어야 서는 것.",
  ]) console.log(`  · ${row}`);

  const fails = results.filter(ok => !ok).length;
  console.log(fails
    ? `\n❌ ${fails}/${results.length} 어긋남 — 굽는 넷의 바이트 꼴만 쟀다(읽개는 안 걸었다)`
    : `\n✅ ${results.length}건 통과 — 굽는 넷의 바이트 꼴만 쟀다(읽개는 안 걸었다)`);
  process.exit(fails ? EXIT_MISMATCH : EXIT_OK);
}
