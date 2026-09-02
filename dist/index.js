const manifest = {"name":"EmuDeck Companion"};
const API_VERSION = 2;
const internalAPIConnection = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
if (!internalAPIConnection) {
    throw new Error('[@decky/api]: Failed to connect to the loader as as the loader API was not initialized. This is likely a bug in Decky Loader.');
}
let api;
try {
    api = internalAPIConnection.connect(API_VERSION, manifest.name);
}
catch {
    api = internalAPIConnection.connect(1, manifest.name);
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version 1. Some features may not work.`);
}
if (api._version != API_VERSION) {
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version ${api._version}. Some features may not work.`);
}
const callable = api.callable;
const toaster = api.toaster;
const definePlugin = (fn) => {
    return (...args) => {
        return fn(...args);
    };
};

var DefaultContext = {
  color: undefined,
  size: undefined,
  className: undefined,
  style: undefined,
  attr: undefined
};
var IconContext = SP_REACT.createContext && /*#__PURE__*/SP_REACT.createContext(DefaultContext);

var _excluded = ["attr", "size", "title"];
function _objectWithoutProperties(e, t) { if (null == e) return {}; var o, r, i = _objectWithoutPropertiesLoose(e, t); if (Object.getOwnPropertySymbols) { var n = Object.getOwnPropertySymbols(e); for (r = 0; r < n.length; r++) o = n[r], -1 === t.indexOf(o) && {}.propertyIsEnumerable.call(e, o) && (i[o] = e[o]); } return i; }
function _objectWithoutPropertiesLoose(r, e) { if (null == r) return {}; var t = {}; for (var n in r) if ({}.hasOwnProperty.call(r, n)) { if (-1 !== e.indexOf(n)) continue; t[n] = r[n]; } return t; }
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), true).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: true, configurable: true, writable: true }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == typeof i ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != typeof t || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r); if ("object" != typeof i) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function Tree2Element(tree) {
  return tree && tree.map((node, i) => /*#__PURE__*/SP_REACT.createElement(node.tag, _objectSpread({
    key: i
  }, node.attr), Tree2Element(node.child)));
}
function GenIcon(data) {
  return props => /*#__PURE__*/SP_REACT.createElement(IconBase, _extends({
    attr: _objectSpread({}, data.attr)
  }, props), Tree2Element(data.child));
}
function IconBase(props) {
  var elem = conf => {
    var attr = props.attr,
      size = props.size,
      title = props.title,
      svgProps = _objectWithoutProperties(props, _excluded);
    var computedSize = size || conf.size || "1em";
    var className;
    if (conf.className) className = conf.className;
    if (props.className) className = (className ? className + " " : "") + props.className;
    return /*#__PURE__*/SP_REACT.createElement("svg", _extends({
      stroke: "currentColor",
      fill: "currentColor",
      strokeWidth: "0"
    }, conf.attr, attr, svgProps, {
      className: className,
      style: _objectSpread(_objectSpread({
        color: props.color || conf.color
      }, conf.style), props.style),
      height: computedSize,
      width: computedSize,
      xmlns: "http://www.w3.org/2000/svg"
    }), title && /*#__PURE__*/SP_REACT.createElement("title", null, title), props.children);
  };
  return IconContext !== undefined ? /*#__PURE__*/SP_REACT.createElement(IconContext.Consumer, null, conf => elem(conf)) : elem(DefaultContext);
}

// THIS FILE IS AUTO GENERATED
function FaGamepad (props) {
  return GenIcon({"attr":{"viewBox":"0 0 640 512"},"child":[{"tag":"path","attr":{"d":"M480.07 96H160a160 160 0 1 0 114.24 272h91.52A160 160 0 1 0 480.07 96zM248 268a12 12 0 0 1-12 12h-52v52a12 12 0 0 1-12 12h-24a12 12 0 0 1-12-12v-52H84a12 12 0 0 1-12-12v-24a12 12 0 0 1 12-12h52v-52a12 12 0 0 1 12-12h24a12 12 0 0 1 12 12v52h52a12 12 0 0 1 12 12zm216 76a40 40 0 1 1 40-40 40 40 0 0 1-40 40zm64-96a40 40 0 1 1 40-40 40 40 0 0 1-40 40z"},"child":[]}]})(props);
}

const getCurrentSession = callable("get_current_session");
const getArtwork = callable("get_artwork");
const executeAction = callable("execute_action");
const refreshDetection = callable("refresh_detection");
const getDiagnostics = callable("get_diagnostics");
callable("reload_profiles");

function Diagnostics({ data, onRefresh }) {
    const rows = [
        ["EmuDeck", data.emudeck.detected ? "Detected" : "Not detected"],
        ["ES-DE", data.emudeck.esde_detected ? "Detected" : "Not detected"],
        ["Emulator", data.session?.emulator_name ?? "None"],
        ["PID", data.session?.pid.toString() ?? "—"],
        ["Game", data.session?.game ?? "—"],
        ["ROM", data.session?.rom ?? "—"],
        ["Input backend", data.input_backend],
        ["Last action", data.last_action?.message ?? "None"],
    ];
    return (SP_JSX.jsxs(DFL.PanelSection, { title: "Diagnostics", children: [rows.map(([label, value]) => (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: { width: "100%" }, children: [SP_JSX.jsx("div", { style: { opacity: 0.55, fontSize: "12px" }, children: label }), SP_JSX.jsx("div", { style: { overflowWrap: "anywhere" }, children: value })] }) }, label))), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => void onRefresh(), children: "Refresh Detection" }) })] }));
}

const groups = [
    { title: "Save States", actions: ["save_state", "load_state"] },
    { title: "Emulation", actions: ["pause", "fast_forward", "rewind"] },
    { title: "Display", actions: ["swap_screen", "lid", "fullscreen"] },
    { title: "Disc", actions: ["previous_disc", "next_disc"] },
    { title: "Other", actions: ["screenshot", "emulator_menu"] },
    { title: "Session", actions: ["quit"] },
];
function stateTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    const today = new Date();
    const sameDay = date.toDateString() === today.toDateString();
    return sameDay
        ? date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        : date.toLocaleDateString([], { month: "short", day: "numeric" });
}
function EmulatorActions({ session, busyAction, onAction }) {
    const supported = new Set(session.capabilities);
    const hasSlots = supported.has("slot_previous") && supported.has("slot_next");
    return (SP_JSX.jsx(SP_JSX.Fragment, { children: groups.map((group) => {
            const actions = group.actions.filter((action) => supported.has(action) && session.actions[action]);
            if (actions.length === 0)
                return null;
            return (SP_JSX.jsxs(DFL.PanelSection, { title: group.title, children: [group.title === "Save States" && hasSlots && (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: { width: "100%", textAlign: "center", opacity: 0.8 }, children: ["Current slot: ", SP_JSX.jsx("b", { children: session.slot })] }) }), session.savestates.slice(0, 5).map((state) => (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: { width: "100%", display: "flex", justifyContent: "space-between", opacity: 0.68, fontSize: "12px" }, children: [SP_JSX.jsx("span", { children: state.slot === null ? "State" : `Slot ${state.slot}` }), SP_JSX.jsx("span", { children: stateTimestamp(state.modified_at) })] }) }, state.path)))] })), actions.map((action) => {
                        const definition = session.actions[action];
                        const active = session.toggles[action];
                        return (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", disabled: busyAction !== null, onClick: () => void onAction(action), children: busyAction === action ? "Working…" : `${definition.label}${active ? " — ON" : ""}` }) }, action));
                    }), group.title === "Save States" && hasSlots && (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", disabled: busyAction !== null, onClick: () => void onAction("slot_previous"), children: "Previous Slot" }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", disabled: busyAction !== null, onClick: () => void onAction("slot_next"), children: "Next Slot" }) })] }))] }, group.title));
        }) }));
}

function elapsed(startedAt) {
    const seconds = Math.max(0, Math.floor(Date.now() / 1000 - startedAt));
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const rest = seconds % 60;
    return [hours, minutes, rest].map((value) => value.toString().padStart(2, "0")).join(":");
}
function GameHeader({ session, artwork }) {
    return (SP_JSX.jsxs("div", { style: { padding: "4px 0 12px" }, children: [artwork && (SP_JSX.jsx("img", { src: artwork, alt: "", style: { width: "100%", maxHeight: "180px", objectFit: "cover", borderRadius: "6px", marginBottom: "10px" } })), SP_JSX.jsx("div", { style: { fontSize: "20px", fontWeight: 700, lineHeight: 1.2 }, children: session.game ?? "Unknown game" }), SP_JSX.jsx("div", { style: { opacity: 0.72, marginTop: "5px" }, children: [session.platform, session.emulator_name].filter(Boolean).join(" • ") }), SP_JSX.jsx("div", { style: { opacity: 0.55, fontVariantNumeric: "tabular-nums", marginTop: "3px" }, children: elapsed(session.started_at) }), session.metadata.desc && (SP_JSX.jsx("div", { style: { opacity: 0.72, fontSize: "12px", lineHeight: 1.35, marginTop: "8px" }, children: session.metadata.desc.length > 220 ? `${session.metadata.desc.slice(0, 217)}…` : session.metadata.desc })), (session.metadata.manual || session.discs.length > 1) && (SP_JSX.jsx("div", { style: { opacity: 0.6, fontSize: "12px", marginTop: "7px" }, children: [session.metadata.manual ? "Manual available" : null, session.discs.length > 1 ? `${session.discs.length} discs` : null]
                    .filter(Boolean).join(" • ") }))] }));
}

var EHIDKeyboardKey;
(function (EHIDKeyboardKey) {
    EHIDKeyboardKey[EHIDKeyboardKey["Invalid"] = 0] = "Invalid";
    EHIDKeyboardKey[EHIDKeyboardKey["BeforeFirst"] = 3] = "BeforeFirst";
    EHIDKeyboardKey[EHIDKeyboardKey["A"] = 4] = "A";
    EHIDKeyboardKey[EHIDKeyboardKey["B"] = 5] = "B";
    EHIDKeyboardKey[EHIDKeyboardKey["C"] = 6] = "C";
    EHIDKeyboardKey[EHIDKeyboardKey["D"] = 7] = "D";
    EHIDKeyboardKey[EHIDKeyboardKey["E"] = 8] = "E";
    EHIDKeyboardKey[EHIDKeyboardKey["F"] = 9] = "F";
    EHIDKeyboardKey[EHIDKeyboardKey["G"] = 10] = "G";
    EHIDKeyboardKey[EHIDKeyboardKey["H"] = 11] = "H";
    EHIDKeyboardKey[EHIDKeyboardKey["I"] = 12] = "I";
    EHIDKeyboardKey[EHIDKeyboardKey["J"] = 13] = "J";
    EHIDKeyboardKey[EHIDKeyboardKey["K"] = 14] = "K";
    EHIDKeyboardKey[EHIDKeyboardKey["L"] = 15] = "L";
    EHIDKeyboardKey[EHIDKeyboardKey["M"] = 16] = "M";
    EHIDKeyboardKey[EHIDKeyboardKey["N"] = 17] = "N";
    EHIDKeyboardKey[EHIDKeyboardKey["O"] = 18] = "O";
    EHIDKeyboardKey[EHIDKeyboardKey["P"] = 19] = "P";
    EHIDKeyboardKey[EHIDKeyboardKey["Q"] = 20] = "Q";
    EHIDKeyboardKey[EHIDKeyboardKey["R"] = 21] = "R";
    EHIDKeyboardKey[EHIDKeyboardKey["S"] = 22] = "S";
    EHIDKeyboardKey[EHIDKeyboardKey["T"] = 23] = "T";
    EHIDKeyboardKey[EHIDKeyboardKey["U"] = 24] = "U";
    EHIDKeyboardKey[EHIDKeyboardKey["V"] = 25] = "V";
    EHIDKeyboardKey[EHIDKeyboardKey["W"] = 26] = "W";
    EHIDKeyboardKey[EHIDKeyboardKey["X"] = 27] = "X";
    EHIDKeyboardKey[EHIDKeyboardKey["Y"] = 28] = "Y";
    EHIDKeyboardKey[EHIDKeyboardKey["Z"] = 29] = "Z";
    EHIDKeyboardKey[EHIDKeyboardKey["Key_1"] = 30] = "Key_1";
    EHIDKeyboardKey[EHIDKeyboardKey["Key_2"] = 31] = "Key_2";
    EHIDKeyboardKey[EHIDKeyboardKey["Key_3"] = 32] = "Key_3";
    EHIDKeyboardKey[EHIDKeyboardKey["Key_4"] = 33] = "Key_4";
    EHIDKeyboardKey[EHIDKeyboardKey["Key_5"] = 34] = "Key_5";
    EHIDKeyboardKey[EHIDKeyboardKey["Key_6"] = 35] = "Key_6";
    EHIDKeyboardKey[EHIDKeyboardKey["Key_7"] = 36] = "Key_7";
    EHIDKeyboardKey[EHIDKeyboardKey["Key_8"] = 37] = "Key_8";
    EHIDKeyboardKey[EHIDKeyboardKey["Key_9"] = 38] = "Key_9";
    EHIDKeyboardKey[EHIDKeyboardKey["Key_0"] = 39] = "Key_0";
    EHIDKeyboardKey[EHIDKeyboardKey["Return"] = 40] = "Return";
    EHIDKeyboardKey[EHIDKeyboardKey["Escape"] = 41] = "Escape";
    EHIDKeyboardKey[EHIDKeyboardKey["Backspace"] = 42] = "Backspace";
    EHIDKeyboardKey[EHIDKeyboardKey["Tab"] = 43] = "Tab";
    EHIDKeyboardKey[EHIDKeyboardKey["Space"] = 44] = "Space";
    EHIDKeyboardKey[EHIDKeyboardKey["Dash"] = 45] = "Dash";
    EHIDKeyboardKey[EHIDKeyboardKey["Equals"] = 46] = "Equals";
    EHIDKeyboardKey[EHIDKeyboardKey["LeftBracket"] = 47] = "LeftBracket";
    EHIDKeyboardKey[EHIDKeyboardKey["RightBracket"] = 48] = "RightBracket";
    EHIDKeyboardKey[EHIDKeyboardKey["Backslash"] = 49] = "Backslash";
    EHIDKeyboardKey[EHIDKeyboardKey["Unused1"] = 50] = "Unused1";
    EHIDKeyboardKey[EHIDKeyboardKey["Semicolon"] = 51] = "Semicolon";
    EHIDKeyboardKey[EHIDKeyboardKey["SingleQuote"] = 52] = "SingleQuote";
    EHIDKeyboardKey[EHIDKeyboardKey["Backtick"] = 53] = "Backtick";
    EHIDKeyboardKey[EHIDKeyboardKey["Comma"] = 54] = "Comma";
    EHIDKeyboardKey[EHIDKeyboardKey["Period"] = 55] = "Period";
    EHIDKeyboardKey[EHIDKeyboardKey["ForwardSlash"] = 56] = "ForwardSlash";
    EHIDKeyboardKey[EHIDKeyboardKey["CapsLock"] = 57] = "CapsLock";
    EHIDKeyboardKey[EHIDKeyboardKey["F1"] = 58] = "F1";
    EHIDKeyboardKey[EHIDKeyboardKey["F2"] = 59] = "F2";
    EHIDKeyboardKey[EHIDKeyboardKey["F3"] = 60] = "F3";
    EHIDKeyboardKey[EHIDKeyboardKey["F4"] = 61] = "F4";
    EHIDKeyboardKey[EHIDKeyboardKey["F5"] = 62] = "F5";
    EHIDKeyboardKey[EHIDKeyboardKey["F6"] = 63] = "F6";
    EHIDKeyboardKey[EHIDKeyboardKey["F7"] = 64] = "F7";
    EHIDKeyboardKey[EHIDKeyboardKey["F8"] = 65] = "F8";
    EHIDKeyboardKey[EHIDKeyboardKey["F9"] = 66] = "F9";
    EHIDKeyboardKey[EHIDKeyboardKey["F10"] = 67] = "F10";
    EHIDKeyboardKey[EHIDKeyboardKey["F11"] = 68] = "F11";
    EHIDKeyboardKey[EHIDKeyboardKey["F12"] = 69] = "F12";
    EHIDKeyboardKey[EHIDKeyboardKey["PrintScreen"] = 70] = "PrintScreen";
    EHIDKeyboardKey[EHIDKeyboardKey["ScrollLock"] = 71] = "ScrollLock";
    EHIDKeyboardKey[EHIDKeyboardKey["Break"] = 72] = "Break";
    EHIDKeyboardKey[EHIDKeyboardKey["Insert"] = 73] = "Insert";
    EHIDKeyboardKey[EHIDKeyboardKey["Home"] = 74] = "Home";
    EHIDKeyboardKey[EHIDKeyboardKey["PageUp"] = 75] = "PageUp";
    EHIDKeyboardKey[EHIDKeyboardKey["Delete"] = 76] = "Delete";
    EHIDKeyboardKey[EHIDKeyboardKey["End"] = 77] = "End";
    EHIDKeyboardKey[EHIDKeyboardKey["PageDown"] = 78] = "PageDown";
    EHIDKeyboardKey[EHIDKeyboardKey["RightArrow"] = 79] = "RightArrow";
    EHIDKeyboardKey[EHIDKeyboardKey["LeftArrow"] = 80] = "LeftArrow";
    EHIDKeyboardKey[EHIDKeyboardKey["DownArrow"] = 81] = "DownArrow";
    EHIDKeyboardKey[EHIDKeyboardKey["UpArrow"] = 82] = "UpArrow";
    EHIDKeyboardKey[EHIDKeyboardKey["NumLock"] = 83] = "NumLock";
    EHIDKeyboardKey[EHIDKeyboardKey["KeypadForwardSlash"] = 84] = "KeypadForwardSlash";
    EHIDKeyboardKey[EHIDKeyboardKey["KeypadAsterisk"] = 85] = "KeypadAsterisk";
    EHIDKeyboardKey[EHIDKeyboardKey["KeypadDash"] = 86] = "KeypadDash";
    EHIDKeyboardKey[EHIDKeyboardKey["KeypadPlus"] = 87] = "KeypadPlus";
    EHIDKeyboardKey[EHIDKeyboardKey["KeypadEnter"] = 88] = "KeypadEnter";
    EHIDKeyboardKey[EHIDKeyboardKey["Keypad_1"] = 89] = "Keypad_1";
    EHIDKeyboardKey[EHIDKeyboardKey["Keypad_2"] = 90] = "Keypad_2";
    EHIDKeyboardKey[EHIDKeyboardKey["Keypad_3"] = 91] = "Keypad_3";
    EHIDKeyboardKey[EHIDKeyboardKey["Keypad_4"] = 92] = "Keypad_4";
    EHIDKeyboardKey[EHIDKeyboardKey["Keypad_5"] = 93] = "Keypad_5";
    EHIDKeyboardKey[EHIDKeyboardKey["Keypad_6"] = 94] = "Keypad_6";
    EHIDKeyboardKey[EHIDKeyboardKey["Keypad_7"] = 95] = "Keypad_7";
    EHIDKeyboardKey[EHIDKeyboardKey["Keypad_8"] = 96] = "Keypad_8";
    EHIDKeyboardKey[EHIDKeyboardKey["Keypad_9"] = 97] = "Keypad_9";
    EHIDKeyboardKey[EHIDKeyboardKey["Keypad_0"] = 98] = "Keypad_0";
    EHIDKeyboardKey[EHIDKeyboardKey["KeypadPeriod"] = 99] = "KeypadPeriod";
    EHIDKeyboardKey[EHIDKeyboardKey["LAlt"] = 100] = "LAlt";
    EHIDKeyboardKey[EHIDKeyboardKey["LShift"] = 101] = "LShift";
    EHIDKeyboardKey[EHIDKeyboardKey["LWin"] = 102] = "LWin";
    EHIDKeyboardKey[EHIDKeyboardKey["LControl"] = 103] = "LControl";
    EHIDKeyboardKey[EHIDKeyboardKey["RAlt"] = 104] = "RAlt";
    EHIDKeyboardKey[EHIDKeyboardKey["RShift"] = 105] = "RShift";
    EHIDKeyboardKey[EHIDKeyboardKey["RWin"] = 106] = "RWin";
    EHIDKeyboardKey[EHIDKeyboardKey["RControl"] = 107] = "RControl";
    EHIDKeyboardKey[EHIDKeyboardKey["VolUp"] = 108] = "VolUp";
    EHIDKeyboardKey[EHIDKeyboardKey["VolDown"] = 109] = "VolDown";
    EHIDKeyboardKey[EHIDKeyboardKey["Mute"] = 110] = "Mute";
    EHIDKeyboardKey[EHIDKeyboardKey["Play"] = 111] = "Play";
    EHIDKeyboardKey[EHIDKeyboardKey["Stop"] = 112] = "Stop";
    EHIDKeyboardKey[EHIDKeyboardKey["Next"] = 113] = "Next";
    EHIDKeyboardKey[EHIDKeyboardKey["Prev"] = 114] = "Prev";
    EHIDKeyboardKey[EHIDKeyboardKey["AfterLast"] = 115] = "AfterLast";
})(EHIDKeyboardKey || (EHIDKeyboardKey = {}));
var EControllerConfigExportType;
(function (EControllerConfigExportType) {
    EControllerConfigExportType[EControllerConfigExportType["Unknown"] = 0] = "Unknown";
    EControllerConfigExportType[EControllerConfigExportType["PersonalLocal"] = 1] = "PersonalLocal";
    EControllerConfigExportType[EControllerConfigExportType["PersonalCloud"] = 2] = "PersonalCloud";
    EControllerConfigExportType[EControllerConfigExportType["Community"] = 3] = "Community";
    EControllerConfigExportType[EControllerConfigExportType["Template"] = 4] = "Template";
    EControllerConfigExportType[EControllerConfigExportType["Official"] = 5] = "Official";
    EControllerConfigExportType[EControllerConfigExportType["OfficialDefault"] = 6] = "OfficialDefault";
})(EControllerConfigExportType || (EControllerConfigExportType = {}));
var EControllerRumbleSetting;
(function (EControllerRumbleSetting) {
    EControllerRumbleSetting[EControllerRumbleSetting["ControllerPreference"] = 0] = "ControllerPreference";
    EControllerRumbleSetting[EControllerRumbleSetting["Off"] = 1] = "Off";
    EControllerRumbleSetting[EControllerRumbleSetting["On"] = 2] = "On";
})(EControllerRumbleSetting || (EControllerRumbleSetting = {}));
var ControllerInputGamepadButton;
(function (ControllerInputGamepadButton) {
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_A"] = 0] = "GAMEPAD_BUTTON_A";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_B"] = 1] = "GAMEPAD_BUTTON_B";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_X"] = 2] = "GAMEPAD_BUTTON_X";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_Y"] = 3] = "GAMEPAD_BUTTON_Y";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_DPAD_UP"] = 4] = "GAMEPAD_BUTTON_DPAD_UP";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_DPAD_RIGHT"] = 5] = "GAMEPAD_BUTTON_DPAD_RIGHT";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_DPAD_DOWN"] = 6] = "GAMEPAD_BUTTON_DPAD_DOWN";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_DPAD_LEFT"] = 7] = "GAMEPAD_BUTTON_DPAD_LEFT";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_MENU"] = 8] = "GAMEPAD_BUTTON_MENU";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_VIEW"] = 9] = "GAMEPAD_BUTTON_VIEW";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LEFTPAD_UP"] = 10] = "GAMEPAD_LEFTPAD_UP";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LEFTPAD_DOWN"] = 11] = "GAMEPAD_LEFTPAD_DOWN";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LEFTPAD_LEFT"] = 12] = "GAMEPAD_LEFTPAD_LEFT";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LEFTPAD_RIGHT"] = 13] = "GAMEPAD_LEFTPAD_RIGHT";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LEFTPAD_ANALOG"] = 14] = "GAMEPAD_LEFTPAD_ANALOG";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_RIGHTPAD_UP"] = 15] = "GAMEPAD_RIGHTPAD_UP";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_RIGHTPAD_DOWN"] = 16] = "GAMEPAD_RIGHTPAD_DOWN";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_RIGHTPAD_LEFT"] = 17] = "GAMEPAD_RIGHTPAD_LEFT";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_RIGHTPAD_RIGHT"] = 18] = "GAMEPAD_RIGHTPAD_RIGHT";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_RIGHTPAD_ANALOG"] = 19] = "GAMEPAD_RIGHTPAD_ANALOG";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LEFTSTICK_UP"] = 20] = "GAMEPAD_LEFTSTICK_UP";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LEFTSTICK_DOWN"] = 21] = "GAMEPAD_LEFTSTICK_DOWN";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LEFTSTICK_LEFT"] = 22] = "GAMEPAD_LEFTSTICK_LEFT";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LEFTSTICK_RIGHT"] = 23] = "GAMEPAD_LEFTSTICK_RIGHT";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LEFTSTICK_ANALOG"] = 24] = "GAMEPAD_LEFTSTICK_ANALOG";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LEFTSTICK_CLICK"] = 25] = "GAMEPAD_LEFTSTICK_CLICK";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LTRIGGER_ANALOG"] = 26] = "GAMEPAD_LTRIGGER_ANALOG";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_RTRIGGER_ANALOG"] = 27] = "GAMEPAD_RTRIGGER_ANALOG";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_LTRIGGER"] = 28] = "GAMEPAD_BUTTON_LTRIGGER";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_RTRIGGER"] = 29] = "GAMEPAD_BUTTON_RTRIGGER";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_LSHOULDER"] = 30] = "GAMEPAD_BUTTON_LSHOULDER";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_RSHOULDER"] = 31] = "GAMEPAD_BUTTON_RSHOULDER";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_LBACK"] = 32] = "GAMEPAD_BUTTON_LBACK";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_RBACK"] = 33] = "GAMEPAD_BUTTON_RBACK";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_GUIDE"] = 34] = "GAMEPAD_BUTTON_GUIDE";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_SELECT"] = 35] = "GAMEPAD_BUTTON_SELECT";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_START"] = 36] = "GAMEPAD_BUTTON_START";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_LPAD_CLICKED"] = 37] = "GAMEPAD_BUTTON_LPAD_CLICKED";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_LPAD_TOUCH"] = 38] = "GAMEPAD_BUTTON_LPAD_TOUCH";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_RPAD_CLICKED"] = 39] = "GAMEPAD_BUTTON_RPAD_CLICKED";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_RPAD_TOUCH"] = 40] = "GAMEPAD_BUTTON_RPAD_TOUCH";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_RIGHTSTICK_CLICK"] = 41] = "GAMEPAD_RIGHTSTICK_CLICK";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_RIGHTSTICK_TOUCH"] = 42] = "GAMEPAD_RIGHTSTICK_TOUCH";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_LEFTSTICK_TOUCH"] = 43] = "GAMEPAD_LEFTSTICK_TOUCH";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_LBACK_UPPER"] = 44] = "GAMEPAD_BUTTON_LBACK_UPPER";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_RBACK_UPPER"] = 45] = "GAMEPAD_BUTTON_RBACK_UPPER";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_BUTTON_LAST"] = 46] = "GAMEPAD_BUTTON_LAST";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_ANALOG_SCROLL"] = 47] = "GAMEPAD_ANALOG_SCROLL";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_ANALOG_LEFT_KEYBOARD_CURSOR"] = 48] = "GAMEPAD_ANALOG_LEFT_KEYBOARD_CURSOR";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_ANALOG_RIGHT_KEYBOARD_CURSOR"] = 49] = "GAMEPAD_ANALOG_RIGHT_KEYBOARD_CURSOR";
    ControllerInputGamepadButton[ControllerInputGamepadButton["GAMEPAD_ANALOG_LAST"] = 50] = "GAMEPAD_ANALOG_LAST";
})(ControllerInputGamepadButton || (ControllerInputGamepadButton = {}));
var EThirdPartyControllerConfiguration;
(function (EThirdPartyControllerConfiguration) {
    EThirdPartyControllerConfiguration[EThirdPartyControllerConfiguration["Off"] = 0] = "Off";
    EThirdPartyControllerConfiguration[EThirdPartyControllerConfiguration["DefaultSetting"] = 1] = "DefaultSetting";
    EThirdPartyControllerConfiguration[EThirdPartyControllerConfiguration["On"] = 2] = "On";
})(EThirdPartyControllerConfiguration || (EThirdPartyControllerConfiguration = {}));
var EControllerType;
(function (EControllerType) {
    EControllerType[EControllerType["None"] = -1] = "None";
    EControllerType[EControllerType["Unknown"] = 0] = "Unknown";
    EControllerType[EControllerType["UnknownSteamController"] = 1] = "UnknownSteamController";
    EControllerType[EControllerType["SteamController"] = 2] = "SteamController";
    EControllerType[EControllerType["SteamControllerV2"] = 3] = "SteamControllerV2";
    EControllerType[EControllerType["SteamControllerNeptune"] = 4] = "SteamControllerNeptune";
    EControllerType[EControllerType["FrontPanelBoard"] = 20] = "FrontPanelBoard";
    EControllerType[EControllerType["Generic"] = 30] = "Generic";
    EControllerType[EControllerType["XBox360Controller"] = 31] = "XBox360Controller";
    EControllerType[EControllerType["XBoxOneController"] = 32] = "XBoxOneController";
    EControllerType[EControllerType["PS3Controller"] = 33] = "PS3Controller";
    EControllerType[EControllerType["PS4Controller"] = 34] = "PS4Controller";
    EControllerType[EControllerType["WiiController"] = 35] = "WiiController";
    EControllerType[EControllerType["AppleController"] = 36] = "AppleController";
    EControllerType[EControllerType["AndroidController"] = 37] = "AndroidController";
    EControllerType[EControllerType["SwitchProController"] = 38] = "SwitchProController";
    EControllerType[EControllerType["SwitchJoyConLeft"] = 39] = "SwitchJoyConLeft";
    EControllerType[EControllerType["SwitchJoyConRight"] = 40] = "SwitchJoyConRight";
    EControllerType[EControllerType["SwitchJoyConPair"] = 41] = "SwitchJoyConPair";
    EControllerType[EControllerType["SwitchProGenericInputOnlyController"] = 42] = "SwitchProGenericInputOnlyController";
    EControllerType[EControllerType["MobileTouch"] = 43] = "MobileTouch";
    EControllerType[EControllerType["SwitchProXInputSwitchController"] = 44] = "SwitchProXInputSwitchController";
    EControllerType[EControllerType["PS5Controller"] = 45] = "PS5Controller";
    EControllerType[EControllerType["XboxEliteController"] = 46] = "XboxEliteController";
    EControllerType[EControllerType["LastController"] = 47] = "LastController";
    EControllerType[EControllerType["PS5EdgeController"] = 48] = "PS5EdgeController";
    EControllerType[EControllerType["GenericKeyboard"] = 400] = "GenericKeyboard";
    EControllerType[EControllerType["GenericMouse"] = 800] = "GenericMouse";
})(EControllerType || (EControllerType = {}));

const keys = {
    a: EHIDKeyboardKey.A,
    d: EHIDKeyboardKey.D,
    f: EHIDKeyboardKey.F,
    p: EHIDKeyboardKey.P,
    r: EHIDKeyboardKey.R,
    enter: EHIDKeyboardKey.Return,
    esc: EHIDKeyboardKey.Escape,
    tab: EHIDKeyboardKey.Tab,
    space: EHIDKeyboardKey.Space,
    insert: EHIDKeyboardKey.Insert,
    home: EHIDKeyboardKey.Home,
    pageup: EHIDKeyboardKey.PageUp,
    end: EHIDKeyboardKey.End,
    f1: EHIDKeyboardKey.F1,
    f2: EHIDKeyboardKey.F2,
    f3: EHIDKeyboardKey.F3,
    f4: EHIDKeyboardKey.F4,
    f5: EHIDKeyboardKey.F5,
    f6: EHIDKeyboardKey.F6,
    f7: EHIDKeyboardKey.F7,
    f8: EHIDKeyboardKey.F8,
    f9: EHIDKeyboardKey.F9,
    f10: EHIDKeyboardKey.F10,
    f11: EHIDKeyboardKey.F11,
    f12: EHIDKeyboardKey.F12,
    leftalt: EHIDKeyboardKey.LAlt,
    leftshift: EHIDKeyboardKey.LShift,
    leftctrl: EHIDKeyboardKey.LControl,
};
function pressHotkeys(names) {
    const mapped = names.map((name) => {
        const key = keys[name.toLowerCase()];
        if (key === undefined)
            throw new Error(`Unsupported Steam Input key: ${name}`);
        return key;
    });
    mapped.forEach((key) => SteamClient.Input.ControllerKeyboardSetKeyState(key, true));
    window.setTimeout(() => {
        [...mapped].reverse().forEach((key) => SteamClient.Input.ControllerKeyboardSetKeyState(key, false));
    }, 100);
}

function Content() {
    const [session, setSession] = SP_REACT.useState(null);
    const [loaded, setLoaded] = SP_REACT.useState(false);
    const [busyAction, setBusyAction] = SP_REACT.useState(null);
    const [showDiagnostics, setShowDiagnostics] = SP_REACT.useState(false);
    const [diagnostics, setDiagnostics] = SP_REACT.useState(null);
    const [artwork, setArtwork] = SP_REACT.useState(null);
    const updateSession = SP_REACT.useCallback(async () => {
        try {
            setSession(await getCurrentSession());
        }
        catch (error) {
            console.error("EmuDeck Companion session refresh failed", error);
        }
        finally {
            setLoaded(true);
        }
    }, []);
    const updateDiagnostics = SP_REACT.useCallback(async () => {
        try {
            setDiagnostics(await getDiagnostics());
        }
        catch (error) {
            toaster.toast({ title: "EmuDeck Companion", body: String(error) });
        }
    }, []);
    SP_REACT.useEffect(() => {
        let disposed = false;
        const poll = async () => {
            if (!disposed)
                await updateSession();
        };
        void poll();
        const timer = window.setInterval(() => void poll(), 1500);
        return () => {
            disposed = true;
            window.clearInterval(timer);
        };
    }, [updateSession]);
    SP_REACT.useEffect(() => {
        let disposed = false;
        setArtwork(null);
        if (session?.metadata.image) {
            void getArtwork().then((value) => {
                if (!disposed)
                    setArtwork(value);
            }).catch((error) => console.error("Artwork loading failed", error));
        }
        return () => { disposed = true; };
    }, [session?.rom, session?.metadata.image]);
    SP_REACT.useEffect(() => {
        if (showDiagnostics)
            void updateDiagnostics();
    }, [showDiagnostics, updateDiagnostics]);
    const onAction = SP_REACT.useCallback(async (action) => {
        if (busyAction !== null)
            return;
        setBusyAction(action);
        try {
            const result = await executeAction(action);
            if (result.ok && result.dispatch === "steam_input" && result.keys) {
                DFL.Navigation.CloseSideMenus();
                window.setTimeout(() => {
                    try {
                        pressHotkeys(result.keys ?? []);
                        toaster.toast({ title: "EmuDeck Companion", body: result.message });
                    }
                    catch (error) {
                        toaster.toast({ title: "Action failed", body: String(error) });
                    }
                }, 200);
            }
            else {
                toaster.toast({
                    title: result.ok ? "EmuDeck Companion" : "Action failed",
                    body: result.message,
                });
                await updateSession();
            }
        }
        catch (error) {
            toaster.toast({ title: "Action failed", body: String(error) });
        }
        finally {
            setBusyAction(null);
        }
    }, [busyAction, updateSession]);
    const manualRefresh = SP_REACT.useCallback(async () => {
        setSession(await refreshDetection());
        if (showDiagnostics)
            await updateDiagnostics();
    }, [showDiagnostics, updateDiagnostics]);
    if (!loaded) {
        return SP_JSX.jsx(DFL.PanelSection, { children: SP_JSX.jsx(DFL.PanelSectionRow, { children: "Detecting active emulator\u2026" }) });
    }
    return (SP_JSX.jsxs(SP_JSX.Fragment, { children: [session ? (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx(DFL.PanelSection, { children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(GameHeader, { session: session, artwork: artwork }) }) }), SP_JSX.jsx(EmulatorActions, { session: session, busyAction: busyAction, onAction: onAction })] })) : (SP_JSX.jsxs(DFL.PanelSection, { title: "EmuDeck Companion", children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { width: "100%", padding: "8px 0", opacity: 0.72 }, children: "No active emulation session" }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => void manualRefresh(), children: "Refresh Detection" }) })] })), SP_JSX.jsx(DFL.PanelSection, { children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => setShowDiagnostics((value) => !value), children: showDiagnostics ? "Hide Diagnostics" : "Show Diagnostics" }) }) }), showDiagnostics && diagnostics && SP_JSX.jsx(Diagnostics, { data: diagnostics, onRefresh: manualRefresh })] }));
}
var index = definePlugin(() => ({
    name: "EmuDeck Companion",
    titleView: SP_JSX.jsx("div", { className: DFL.staticClasses.Title, children: "EmuDeck Companion" }),
    content: SP_JSX.jsx(Content, {}),
    icon: SP_JSX.jsx(FaGamepad, {}),
    onDismount() {
        console.log("EmuDeck Companion unloaded");
    },
}));

export { index as default };
//# sourceMappingURL=index.js.map
