import { Badge, Button, Codicon, ConfirmDialog, DEFAULT_REASONING_EFFORT, DisclosureCaret, DropdownMenu, DropdownMenuContent, DropdownMenuTrigger, MessageTextContent, ModelCatalogMenu, ModelMenuCloseContext, PanelAction, PanelBlock, PanelDetail, PanelEmpty, PanelHeader, PanelList, PanelListRow, PanelMeta, PanelPill, PanelSectionLabel, ROUTES_AREA, RowButton, SIDEBAR_NAV_AREA, SegmentedControl, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, THEMES_AREA, cn, host, reasoningEffortLabel, useValue } from "@hermes/plugin-sdk";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
//#region \0rolldown/runtime.js
var __defProp$1 = Object.defineProperty;
var __exportAll$1 = (all, no_symbols) => {
	let target = {};
	for (var name in all) __defProp$1(target, name, {
		get: all[name],
		enumerable: true
	});
	if (!no_symbols) __defProp$1(target, Symbol.toStringTag, { value: "Module" });
	return target;
};
//#endregion
//#region hermes-plugin/plugins/themis/assets/pdfjs/pdfjs-viewer.bundle.mjs
var pdfjs_viewer_bundle_exports = /* @__PURE__ */ __exportAll$1({
	EventBus: () => EventBus,
	GlobalWorkerOptions: () => GlobalWorkerOptions,
	PDFFindController: () => PDFFindController,
	PDFLinkService: () => PDFLinkService,
	PDFRenderingQueue: () => PDFRenderingQueue,
	PDFViewer: () => PDFViewer,
	getDocument: () => getDocument,
	version: () => version
});
var __defProp = Object.defineProperty;
var __esmMin = (fn, res, err) => () => {
	if (err) throw err[0];
	try {
		return fn && (res = fn(fn = 0)), res;
	} catch (e) {
		throw err = [e], e;
	}
};
var __exportAll = (all, no_symbols) => {
	let target = {};
	for (var name in all) __defProp(target, name, {
		get: all[name],
		enumerable: true
	});
	if (!no_symbols) __defProp(target, Symbol.toStringTag, { value: "Module" });
	return target;
};
var pdf_exports = /* @__PURE__ */ __exportAll({
	AbortException: () => __webpack_exports__AbortException,
	AnnotationEditorLayer: () => __webpack_exports__AnnotationEditorLayer,
	AnnotationEditorParamsType: () => __webpack_exports__AnnotationEditorParamsType,
	AnnotationEditorType: () => __webpack_exports__AnnotationEditorType,
	AnnotationEditorUIManager: () => __webpack_exports__AnnotationEditorUIManager,
	AnnotationLayer: () => __webpack_exports__AnnotationLayer,
	AnnotationMode: () => __webpack_exports__AnnotationMode,
	ColorPicker: () => __webpack_exports__ColorPicker,
	DOMSVGFactory: () => __webpack_exports__DOMSVGFactory,
	DrawLayer: () => __webpack_exports__DrawLayer,
	FeatureTest: () => __webpack_exports__FeatureTest,
	GlobalWorkerOptions: () => __webpack_exports__GlobalWorkerOptions,
	ImageKind: () => __webpack_exports__ImageKind,
	InvalidPDFException: () => __webpack_exports__InvalidPDFException,
	MissingPDFException: () => __webpack_exports__MissingPDFException,
	OPS: () => __webpack_exports__OPS,
	OutputScale: () => __webpack_exports__OutputScale,
	PDFDataRangeTransport: () => __webpack_exports__PDFDataRangeTransport,
	PDFDateString: () => __webpack_exports__PDFDateString,
	PDFWorker: () => __webpack_exports__PDFWorker,
	PasswordResponses: () => __webpack_exports__PasswordResponses,
	PermissionFlag: () => __webpack_exports__PermissionFlag,
	PixelsPerInch: () => __webpack_exports__PixelsPerInch,
	RenderingCancelledException: () => __webpack_exports__RenderingCancelledException,
	TextLayer: () => __webpack_exports__TextLayer,
	TouchManager: () => __webpack_exports__TouchManager,
	UnexpectedResponseException: () => __webpack_exports__UnexpectedResponseException,
	Util: () => __webpack_exports__Util,
	VerbosityLevel: () => __webpack_exports__VerbosityLevel,
	XfaLayer: () => __webpack_exports__XfaLayer,
	build: () => __webpack_exports__build,
	createValidAbsoluteUrl: () => __webpack_exports__createValidAbsoluteUrl,
	fetchData: () => __webpack_exports__fetchData,
	getDocument: () => __webpack_exports__getDocument,
	getFilenameFromUrl: () => __webpack_exports__getFilenameFromUrl,
	getPdfFilenameFromUrl: () => __webpack_exports__getPdfFilenameFromUrl,
	getXfaPageViewport: () => __webpack_exports__getXfaPageViewport,
	isDataScheme: () => __webpack_exports__isDataScheme,
	isPdfFile: () => __webpack_exports__isPdfFile,
	noContextMenu: () => __webpack_exports__noContextMenu,
	normalizeUnicode: () => __webpack_exports__normalizeUnicode,
	setLayerDimensions: () => __webpack_exports__setLayerDimensions,
	shadow: () => __webpack_exports__shadow,
	stopEvent: () => __webpack_exports__stopEvent,
	version: () => __webpack_exports__version
});
/**
* @licstart The following is the entire license notice for the
* JavaScript code in this page
*
* Copyright 2024 Mozilla Foundation
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*
* @licend The above is the entire license notice for the
* JavaScript code in this page
*/
var __webpack_require__$1 = {};
(() => {
	__webpack_require__$1.d = (exports, definition) => {
		for (var key in definition) if (__webpack_require__$1.o(definition, key) && !__webpack_require__$1.o(exports, key)) Object.defineProperty(exports, key, {
			enumerable: true,
			get: definition[key]
		});
	};
})();
(() => {
	__webpack_require__$1.o = (obj, prop) => Object.prototype.hasOwnProperty.call(obj, prop);
})();
var __webpack_exports__$1 = globalThis.pdfjsLib = {};
__webpack_require__$1.d(__webpack_exports__$1, {
	AbortException: () => AbortException$1,
	AnnotationEditorLayer: () => AnnotationEditorLayer$1,
	AnnotationEditorParamsType: () => AnnotationEditorParamsType$1,
	AnnotationEditorType: () => AnnotationEditorType$1,
	AnnotationEditorUIManager: () => AnnotationEditorUIManager$1,
	AnnotationLayer: () => AnnotationLayer$1,
	AnnotationMode: () => AnnotationMode$1,
	ColorPicker: () => ColorPicker$1,
	DOMSVGFactory: () => DOMSVGFactory$1,
	DrawLayer: () => DrawLayer$1,
	FeatureTest: () => util_FeatureTest,
	GlobalWorkerOptions: () => GlobalWorkerOptions$2,
	ImageKind: () => util_ImageKind,
	InvalidPDFException: () => InvalidPDFException$1,
	MissingPDFException: () => MissingPDFException$1,
	OPS: () => OPS$1,
	OutputScale: () => OutputScale$1,
	PDFDataRangeTransport: () => PDFDataRangeTransport$1,
	PDFDateString: () => PDFDateString$1,
	PDFWorker: () => PDFWorker$1,
	PasswordResponses: () => PasswordResponses$1,
	PermissionFlag: () => PermissionFlag$1,
	PixelsPerInch: () => PixelsPerInch$1,
	RenderingCancelledException: () => RenderingCancelledException$1,
	TextLayer: () => TextLayer$1,
	TouchManager: () => TouchManager$1,
	UnexpectedResponseException: () => UnexpectedResponseException$1,
	Util: () => Util$1,
	VerbosityLevel: () => VerbosityLevel$1,
	XfaLayer: () => XfaLayer$1,
	build: () => build$1,
	createValidAbsoluteUrl: () => createValidAbsoluteUrl$1,
	fetchData: () => fetchData$1,
	getDocument: () => getDocument$2,
	getFilenameFromUrl: () => getFilenameFromUrl$1,
	getPdfFilenameFromUrl: () => getPdfFilenameFromUrl$1,
	getXfaPageViewport: () => getXfaPageViewport$1,
	isDataScheme: () => isDataScheme$1,
	isPdfFile: () => isPdfFile$1,
	noContextMenu: () => noContextMenu$1,
	normalizeUnicode: () => normalizeUnicode$1,
	setLayerDimensions: () => setLayerDimensions$1,
	shadow: () => shadow$1,
	stopEvent: () => stopEvent$1,
	version: () => version$2
});
var isNodeJS = typeof process === "object" && process + "" === "[object process]" && !process.versions.nw && !(process.versions.electron && process.type && process.type !== "browser");
var IDENTITY_MATRIX = [
	1,
	0,
	0,
	1,
	0,
	0
];
var FONT_IDENTITY_MATRIX = [
	.001,
	0,
	0,
	.001,
	0,
	0
];
var MAX_IMAGE_SIZE_TO_CACHE = 1e7;
var LINE_FACTOR = 1.35;
var RenderingIntentFlag = {
	ANY: 1,
	DISPLAY: 2,
	PRINT: 4,
	SAVE: 8,
	ANNOTATIONS_FORMS: 16,
	ANNOTATIONS_STORAGE: 32,
	ANNOTATIONS_DISABLE: 64,
	IS_EDITING: 128,
	OPLIST: 256
};
var AnnotationMode$1 = {
	DISABLE: 0,
	ENABLE: 1,
	ENABLE_FORMS: 2,
	ENABLE_STORAGE: 3
};
var AnnotationEditorPrefix = "pdfjs_internal_editor_";
var AnnotationEditorType$1 = {
	DISABLE: -1,
	NONE: 0,
	FREETEXT: 3,
	HIGHLIGHT: 9,
	STAMP: 13,
	INK: 15
};
var AnnotationEditorParamsType$1 = {
	RESIZE: 1,
	CREATE: 2,
	FREETEXT_SIZE: 11,
	FREETEXT_COLOR: 12,
	FREETEXT_OPACITY: 13,
	INK_COLOR: 21,
	INK_THICKNESS: 22,
	INK_OPACITY: 23,
	HIGHLIGHT_COLOR: 31,
	HIGHLIGHT_DEFAULT_COLOR: 32,
	HIGHLIGHT_THICKNESS: 33,
	HIGHLIGHT_FREE: 34,
	HIGHLIGHT_SHOW_ALL: 35,
	DRAW_STEP: 41
};
var PermissionFlag$1 = {
	PRINT: 4,
	MODIFY_CONTENTS: 8,
	COPY: 16,
	MODIFY_ANNOTATIONS: 32,
	FILL_INTERACTIVE_FORMS: 256,
	COPY_FOR_ACCESSIBILITY: 512,
	ASSEMBLE: 1024,
	PRINT_HIGH_QUALITY: 2048
};
var TextRenderingMode = {
	FILL: 0,
	STROKE: 1,
	FILL_STROKE: 2,
	INVISIBLE: 3,
	FILL_ADD_TO_PATH: 4,
	STROKE_ADD_TO_PATH: 5,
	FILL_STROKE_ADD_TO_PATH: 6,
	ADD_TO_PATH: 7,
	FILL_STROKE_MASK: 3,
	ADD_TO_PATH_FLAG: 4
};
var util_ImageKind = {
	GRAYSCALE_1BPP: 1,
	RGB_24BPP: 2,
	RGBA_32BPP: 3
};
var AnnotationType = {
	TEXT: 1,
	LINK: 2,
	FREETEXT: 3,
	LINE: 4,
	SQUARE: 5,
	CIRCLE: 6,
	POLYGON: 7,
	POLYLINE: 8,
	HIGHLIGHT: 9,
	UNDERLINE: 10,
	SQUIGGLY: 11,
	STRIKEOUT: 12,
	STAMP: 13,
	CARET: 14,
	INK: 15,
	POPUP: 16,
	FILEATTACHMENT: 17,
	SOUND: 18,
	MOVIE: 19,
	WIDGET: 20,
	SCREEN: 21,
	PRINTERMARK: 22,
	TRAPNET: 23,
	WATERMARK: 24,
	THREED: 25,
	REDACT: 26
};
var AnnotationBorderStyleType = {
	SOLID: 1,
	DASHED: 2,
	BEVELED: 3,
	INSET: 4,
	UNDERLINE: 5
};
var VerbosityLevel$1 = {
	ERRORS: 0,
	WARNINGS: 1,
	INFOS: 5
};
var OPS$1 = {
	dependency: 1,
	setLineWidth: 2,
	setLineCap: 3,
	setLineJoin: 4,
	setMiterLimit: 5,
	setDash: 6,
	setRenderingIntent: 7,
	setFlatness: 8,
	setGState: 9,
	save: 10,
	restore: 11,
	transform: 12,
	moveTo: 13,
	lineTo: 14,
	curveTo: 15,
	curveTo2: 16,
	curveTo3: 17,
	closePath: 18,
	rectangle: 19,
	stroke: 20,
	closeStroke: 21,
	fill: 22,
	eoFill: 23,
	fillStroke: 24,
	eoFillStroke: 25,
	closeFillStroke: 26,
	closeEOFillStroke: 27,
	endPath: 28,
	clip: 29,
	eoClip: 30,
	beginText: 31,
	endText: 32,
	setCharSpacing: 33,
	setWordSpacing: 34,
	setHScale: 35,
	setLeading: 36,
	setFont: 37,
	setTextRenderingMode: 38,
	setTextRise: 39,
	moveText: 40,
	setLeadingMoveText: 41,
	setTextMatrix: 42,
	nextLine: 43,
	showText: 44,
	showSpacedText: 45,
	nextLineShowText: 46,
	nextLineSetSpacingShowText: 47,
	setCharWidth: 48,
	setCharWidthAndBounds: 49,
	setStrokeColorSpace: 50,
	setFillColorSpace: 51,
	setStrokeColor: 52,
	setStrokeColorN: 53,
	setFillColor: 54,
	setFillColorN: 55,
	setStrokeGray: 56,
	setFillGray: 57,
	setStrokeRGBColor: 58,
	setFillRGBColor: 59,
	setStrokeCMYKColor: 60,
	setFillCMYKColor: 61,
	shadingFill: 62,
	beginInlineImage: 63,
	beginImageData: 64,
	endInlineImage: 65,
	paintXObject: 66,
	markPoint: 67,
	markPointProps: 68,
	beginMarkedContent: 69,
	beginMarkedContentProps: 70,
	endMarkedContent: 71,
	beginCompat: 72,
	endCompat: 73,
	paintFormXObjectBegin: 74,
	paintFormXObjectEnd: 75,
	beginGroup: 76,
	endGroup: 77,
	beginAnnotation: 80,
	endAnnotation: 81,
	paintImageMaskXObject: 83,
	paintImageMaskXObjectGroup: 84,
	paintImageXObject: 85,
	paintInlineImageXObject: 86,
	paintInlineImageXObjectGroup: 87,
	paintImageXObjectRepeat: 88,
	paintImageMaskXObjectRepeat: 89,
	paintSolidColorImageMask: 90,
	constructPath: 91,
	setStrokeTransparent: 92,
	setFillTransparent: 93
};
var PasswordResponses$1 = {
	NEED_PASSWORD: 1,
	INCORRECT_PASSWORD: 2
};
var verbosity = VerbosityLevel$1.WARNINGS;
function setVerbosityLevel(level) {
	if (Number.isInteger(level)) verbosity = level;
}
function getVerbosityLevel() {
	return verbosity;
}
function info(msg) {
	if (verbosity >= VerbosityLevel$1.INFOS) console.log(`Info: ${msg}`);
}
function warn(msg) {
	if (verbosity >= VerbosityLevel$1.WARNINGS) console.log(`Warning: ${msg}`);
}
function unreachable(msg) {
	throw new Error(msg);
}
function assert(cond, msg) {
	if (!cond) unreachable(msg);
}
function _isValidProtocol(url) {
	switch (url?.protocol) {
		case "http:":
		case "https:":
		case "ftp:":
		case "mailto:":
		case "tel:": return true;
		default: return false;
	}
}
function createValidAbsoluteUrl$1(url, baseUrl = null, options = null) {
	if (!url) return null;
	try {
		if (options && typeof url === "string") {
			if (options.addDefaultProtocol && url.startsWith("www.")) {
				if (url.match(/\./g)?.length >= 2) url = `http://${url}`;
			}
			if (options.tryConvertEncoding) try {
				url = stringToUTF8String(url);
			} catch {}
		}
		const absoluteUrl = baseUrl ? new URL(url, baseUrl) : new URL(url);
		if (_isValidProtocol(absoluteUrl)) return absoluteUrl;
	} catch {}
	return null;
}
function shadow$1(obj, prop, value, nonSerializable = false) {
	Object.defineProperty(obj, prop, {
		value,
		enumerable: !nonSerializable,
		configurable: true,
		writable: false
	});
	return value;
}
var BaseException = function BaseExceptionClosure() {
	function BaseException(message, name) {
		this.message = message;
		this.name = name;
	}
	BaseException.prototype = /* @__PURE__ */ new Error();
	BaseException.constructor = BaseException;
	return BaseException;
}();
var PasswordException = class extends BaseException {
	constructor(msg, code) {
		super(msg, "PasswordException");
		this.code = code;
	}
};
var UnknownErrorException = class extends BaseException {
	constructor(msg, details) {
		super(msg, "UnknownErrorException");
		this.details = details;
	}
};
var InvalidPDFException$1 = class extends BaseException {
	constructor(msg) {
		super(msg, "InvalidPDFException");
	}
};
var MissingPDFException$1 = class extends BaseException {
	constructor(msg) {
		super(msg, "MissingPDFException");
	}
};
var UnexpectedResponseException$1 = class extends BaseException {
	constructor(msg, status) {
		super(msg, "UnexpectedResponseException");
		this.status = status;
	}
};
var FormatError = class extends BaseException {
	constructor(msg) {
		super(msg, "FormatError");
	}
};
var AbortException$1 = class extends BaseException {
	constructor(msg) {
		super(msg, "AbortException");
	}
};
function bytesToString(bytes) {
	if (typeof bytes !== "object" || bytes?.length === void 0) unreachable("Invalid argument for bytesToString");
	const length = bytes.length;
	const MAX_ARGUMENT_COUNT = 8192;
	if (length < MAX_ARGUMENT_COUNT) return String.fromCharCode.apply(null, bytes);
	const strBuf = [];
	for (let i = 0; i < length; i += MAX_ARGUMENT_COUNT) {
		const chunkEnd = Math.min(i + MAX_ARGUMENT_COUNT, length);
		const chunk = bytes.subarray(i, chunkEnd);
		strBuf.push(String.fromCharCode.apply(null, chunk));
	}
	return strBuf.join("");
}
function stringToBytes(str) {
	if (typeof str !== "string") unreachable("Invalid argument for stringToBytes");
	const length = str.length;
	const bytes = new Uint8Array(length);
	for (let i = 0; i < length; ++i) bytes[i] = str.charCodeAt(i) & 255;
	return bytes;
}
function string32(value) {
	return String.fromCharCode(value >> 24 & 255, value >> 16 & 255, value >> 8 & 255, value & 255);
}
function objectFromMap(map) {
	const obj = Object.create(null);
	for (const [key, value] of map) obj[key] = value;
	return obj;
}
function isLittleEndian() {
	const buffer8 = /* @__PURE__ */ new Uint8Array(4);
	buffer8[0] = 1;
	return new Uint32Array(buffer8.buffer, 0, 1)[0] === 1;
}
function isEvalSupported() {
	return false;
}
var util_FeatureTest = class {
	static get isLittleEndian() {
		return shadow$1(this, "isLittleEndian", isLittleEndian());
	}
	static get isEvalSupported() {
		return shadow$1(this, "isEvalSupported", isEvalSupported());
	}
	static get isOffscreenCanvasSupported() {
		return shadow$1(this, "isOffscreenCanvasSupported", typeof OffscreenCanvas !== "undefined");
	}
	static get isImageDecoderSupported() {
		return shadow$1(this, "isImageDecoderSupported", typeof ImageDecoder !== "undefined");
	}
	static get platform() {
		if (typeof navigator !== "undefined" && typeof navigator?.platform === "string") return shadow$1(this, "platform", {
			isMac: navigator.platform.includes("Mac"),
			isWindows: navigator.platform.includes("Win"),
			isFirefox: typeof navigator?.userAgent === "string" && navigator.userAgent.includes("Firefox")
		});
		return shadow$1(this, "platform", {
			isMac: false,
			isWindows: false,
			isFirefox: false
		});
	}
	static get isCSSRoundSupported() {
		return shadow$1(this, "isCSSRoundSupported", globalThis.CSS?.supports?.("width: round(1.5px, 1px)"));
	}
};
var hexNumbers = Array.from(Array(256).keys(), (n) => n.toString(16).padStart(2, "0"));
var Util$1 = class {
	static makeHexColor(r, g, b) {
		return `#${hexNumbers[r]}${hexNumbers[g]}${hexNumbers[b]}`;
	}
	static scaleMinMax(transform, minMax) {
		let temp;
		if (transform[0]) {
			if (transform[0] < 0) {
				temp = minMax[0];
				minMax[0] = minMax[2];
				minMax[2] = temp;
			}
			minMax[0] *= transform[0];
			minMax[2] *= transform[0];
			if (transform[3] < 0) {
				temp = minMax[1];
				minMax[1] = minMax[3];
				minMax[3] = temp;
			}
			minMax[1] *= transform[3];
			minMax[3] *= transform[3];
		} else {
			temp = minMax[0];
			minMax[0] = minMax[1];
			minMax[1] = temp;
			temp = minMax[2];
			minMax[2] = minMax[3];
			minMax[3] = temp;
			if (transform[1] < 0) {
				temp = minMax[1];
				minMax[1] = minMax[3];
				minMax[3] = temp;
			}
			minMax[1] *= transform[1];
			minMax[3] *= transform[1];
			if (transform[2] < 0) {
				temp = minMax[0];
				minMax[0] = minMax[2];
				minMax[2] = temp;
			}
			minMax[0] *= transform[2];
			minMax[2] *= transform[2];
		}
		minMax[0] += transform[4];
		minMax[1] += transform[5];
		minMax[2] += transform[4];
		minMax[3] += transform[5];
	}
	static transform(m1, m2) {
		return [
			m1[0] * m2[0] + m1[2] * m2[1],
			m1[1] * m2[0] + m1[3] * m2[1],
			m1[0] * m2[2] + m1[2] * m2[3],
			m1[1] * m2[2] + m1[3] * m2[3],
			m1[0] * m2[4] + m1[2] * m2[5] + m1[4],
			m1[1] * m2[4] + m1[3] * m2[5] + m1[5]
		];
	}
	static applyTransform(p, m) {
		return [p[0] * m[0] + p[1] * m[2] + m[4], p[0] * m[1] + p[1] * m[3] + m[5]];
	}
	static applyInverseTransform(p, m) {
		const d = m[0] * m[3] - m[1] * m[2];
		return [(p[0] * m[3] - p[1] * m[2] + m[2] * m[5] - m[4] * m[3]) / d, (-p[0] * m[1] + p[1] * m[0] + m[4] * m[1] - m[5] * m[0]) / d];
	}
	static getAxialAlignedBoundingBox(r, m) {
		const p1 = this.applyTransform(r, m);
		const p2 = this.applyTransform(r.slice(2, 4), m);
		const p3 = this.applyTransform([r[0], r[3]], m);
		const p4 = this.applyTransform([r[2], r[1]], m);
		return [
			Math.min(p1[0], p2[0], p3[0], p4[0]),
			Math.min(p1[1], p2[1], p3[1], p4[1]),
			Math.max(p1[0], p2[0], p3[0], p4[0]),
			Math.max(p1[1], p2[1], p3[1], p4[1])
		];
	}
	static inverseTransform(m) {
		const d = m[0] * m[3] - m[1] * m[2];
		return [
			m[3] / d,
			-m[1] / d,
			-m[2] / d,
			m[0] / d,
			(m[2] * m[5] - m[4] * m[3]) / d,
			(m[4] * m[1] - m[5] * m[0]) / d
		];
	}
	static singularValueDecompose2dScale(m) {
		const transpose = [
			m[0],
			m[2],
			m[1],
			m[3]
		];
		const a = m[0] * transpose[0] + m[1] * transpose[2];
		const b = m[0] * transpose[1] + m[1] * transpose[3];
		const c = m[2] * transpose[0] + m[3] * transpose[2];
		const d = m[2] * transpose[1] + m[3] * transpose[3];
		const first = (a + d) / 2;
		const second = Math.sqrt((a + d) ** 2 - 4 * (a * d - c * b)) / 2;
		const sx = first + second || 1;
		const sy = first - second || 1;
		return [Math.sqrt(sx), Math.sqrt(sy)];
	}
	static normalizeRect(rect) {
		const r = rect.slice(0);
		if (rect[0] > rect[2]) {
			r[0] = rect[2];
			r[2] = rect[0];
		}
		if (rect[1] > rect[3]) {
			r[1] = rect[3];
			r[3] = rect[1];
		}
		return r;
	}
	static intersect(rect1, rect2) {
		const xLow = Math.max(Math.min(rect1[0], rect1[2]), Math.min(rect2[0], rect2[2]));
		const xHigh = Math.min(Math.max(rect1[0], rect1[2]), Math.max(rect2[0], rect2[2]));
		if (xLow > xHigh) return null;
		const yLow = Math.max(Math.min(rect1[1], rect1[3]), Math.min(rect2[1], rect2[3]));
		const yHigh = Math.min(Math.max(rect1[1], rect1[3]), Math.max(rect2[1], rect2[3]));
		if (yLow > yHigh) return null;
		return [
			xLow,
			yLow,
			xHigh,
			yHigh
		];
	}
	static #getExtremumOnCurve(x0, x1, x2, x3, y0, y1, y2, y3, t, minMax) {
		if (t <= 0 || t >= 1) return;
		const mt = 1 - t;
		const tt = t * t;
		const ttt = tt * t;
		const x = mt * (mt * (mt * x0 + 3 * t * x1) + 3 * tt * x2) + ttt * x3;
		const y = mt * (mt * (mt * y0 + 3 * t * y1) + 3 * tt * y2) + ttt * y3;
		minMax[0] = Math.min(minMax[0], x);
		minMax[1] = Math.min(minMax[1], y);
		minMax[2] = Math.max(minMax[2], x);
		minMax[3] = Math.max(minMax[3], y);
	}
	static #getExtremum(x0, x1, x2, x3, y0, y1, y2, y3, a, b, c, minMax) {
		if (Math.abs(a) < 1e-12) {
			if (Math.abs(b) >= 1e-12) this.#getExtremumOnCurve(x0, x1, x2, x3, y0, y1, y2, y3, -c / b, minMax);
			return;
		}
		const delta = b ** 2 - 4 * c * a;
		if (delta < 0) return;
		const sqrtDelta = Math.sqrt(delta);
		const a2 = 2 * a;
		this.#getExtremumOnCurve(x0, x1, x2, x3, y0, y1, y2, y3, (-b + sqrtDelta) / a2, minMax);
		this.#getExtremumOnCurve(x0, x1, x2, x3, y0, y1, y2, y3, (-b - sqrtDelta) / a2, minMax);
	}
	static bezierBoundingBox(x0, y0, x1, y1, x2, y2, x3, y3, minMax) {
		if (minMax) {
			minMax[0] = Math.min(minMax[0], x0, x3);
			minMax[1] = Math.min(minMax[1], y0, y3);
			minMax[2] = Math.max(minMax[2], x0, x3);
			minMax[3] = Math.max(minMax[3], y0, y3);
		} else minMax = [
			Math.min(x0, x3),
			Math.min(y0, y3),
			Math.max(x0, x3),
			Math.max(y0, y3)
		];
		this.#getExtremum(x0, x1, x2, x3, y0, y1, y2, y3, 3 * (-x0 + 3 * (x1 - x2) + x3), 6 * (x0 - 2 * x1 + x2), 3 * (x1 - x0), minMax);
		this.#getExtremum(x0, x1, x2, x3, y0, y1, y2, y3, 3 * (-y0 + 3 * (y1 - y2) + y3), 6 * (y0 - 2 * y1 + y2), 3 * (y1 - y0), minMax);
		return minMax;
	}
};
function stringToUTF8String(str) {
	return decodeURIComponent(escape(str));
}
var NormalizeRegex = null;
var NormalizationMap = null;
function normalizeUnicode$1(str) {
	if (!NormalizeRegex) {
		NormalizeRegex = /([\u00a0\u00b5\u037e\u0eb3\u2000-\u200a\u202f\u2126\ufb00-\ufb04\ufb06\ufb20-\ufb36\ufb38-\ufb3c\ufb3e\ufb40-\ufb41\ufb43-\ufb44\ufb46-\ufba1\ufba4-\ufba9\ufbae-\ufbb1\ufbd3-\ufbdc\ufbde-\ufbe7\ufbea-\ufbf8\ufbfc-\ufbfd\ufc00-\ufc5d\ufc64-\ufcf1\ufcf5-\ufd3d\ufd88\ufdf4\ufdfa-\ufdfb\ufe71\ufe77\ufe79\ufe7b\ufe7d]+)|(\ufb05+)/gu;
		NormalizationMap = /* @__PURE__ */ new Map([["ﬅ", "ſt"]]);
	}
	return str.replaceAll(NormalizeRegex, (_, p1, p2) => p1 ? p1.normalize("NFKC") : NormalizationMap.get(p2));
}
function getUuid() {
	if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
	const buf = /* @__PURE__ */ new Uint8Array(32);
	crypto.getRandomValues(buf);
	return bytesToString(buf);
}
var AnnotationPrefix = "pdfjs_internal_id_";
function toBase64Util(arr) {
	if (Uint8Array.prototype.toBase64) return arr.toBase64();
	return btoa(bytesToString(arr));
}
if (typeof Promise.try !== "function") Promise.try = function(fn, ...args) {
	return new Promise((resolve) => {
		resolve(fn(...args));
	});
};
var SVG_NS = "http://www.w3.org/2000/svg";
var PixelsPerInch$1 = class {
	static CSS = 96;
	static PDF = 72;
	static PDF_TO_CSS_UNITS = this.CSS / this.PDF;
};
async function fetchData$1(url, type = "text") {
	if (isValidFetchUrl(url, document.baseURI)) {
		const response = await fetch(url);
		if (!response.ok) throw new Error(response.statusText);
		switch (type) {
			case "arraybuffer": return response.arrayBuffer();
			case "blob": return response.blob();
			case "json": return response.json();
		}
		return response.text();
	}
	return new Promise((resolve, reject) => {
		const request = new XMLHttpRequest();
		request.open("GET", url, true);
		request.responseType = type;
		request.onreadystatechange = () => {
			if (request.readyState !== XMLHttpRequest.DONE) return;
			if (request.status === 200 || request.status === 0) {
				switch (type) {
					case "arraybuffer":
					case "blob":
					case "json":
						resolve(request.response);
						return;
				}
				resolve(request.responseText);
				return;
			}
			reject(new Error(request.statusText));
		};
		request.send(null);
	});
}
var PageViewport = class PageViewport {
	constructor({ viewBox, userUnit, scale, rotation, offsetX = 0, offsetY = 0, dontFlip = false }) {
		this.viewBox = viewBox;
		this.userUnit = userUnit;
		this.scale = scale;
		this.rotation = rotation;
		this.offsetX = offsetX;
		this.offsetY = offsetY;
		scale *= userUnit;
		const centerX = (viewBox[2] + viewBox[0]) / 2;
		const centerY = (viewBox[3] + viewBox[1]) / 2;
		let rotateA, rotateB, rotateC, rotateD;
		rotation %= 360;
		if (rotation < 0) rotation += 360;
		switch (rotation) {
			case 180:
				rotateA = -1;
				rotateB = 0;
				rotateC = 0;
				rotateD = 1;
				break;
			case 90:
				rotateA = 0;
				rotateB = 1;
				rotateC = 1;
				rotateD = 0;
				break;
			case 270:
				rotateA = 0;
				rotateB = -1;
				rotateC = -1;
				rotateD = 0;
				break;
			case 0:
				rotateA = 1;
				rotateB = 0;
				rotateC = 0;
				rotateD = -1;
				break;
			default: throw new Error("PageViewport: Invalid rotation, must be a multiple of 90 degrees.");
		}
		if (dontFlip) {
			rotateC = -rotateC;
			rotateD = -rotateD;
		}
		let offsetCanvasX, offsetCanvasY;
		let width, height;
		if (rotateA === 0) {
			offsetCanvasX = Math.abs(centerY - viewBox[1]) * scale + offsetX;
			offsetCanvasY = Math.abs(centerX - viewBox[0]) * scale + offsetY;
			width = (viewBox[3] - viewBox[1]) * scale;
			height = (viewBox[2] - viewBox[0]) * scale;
		} else {
			offsetCanvasX = Math.abs(centerX - viewBox[0]) * scale + offsetX;
			offsetCanvasY = Math.abs(centerY - viewBox[1]) * scale + offsetY;
			width = (viewBox[2] - viewBox[0]) * scale;
			height = (viewBox[3] - viewBox[1]) * scale;
		}
		this.transform = [
			rotateA * scale,
			rotateB * scale,
			rotateC * scale,
			rotateD * scale,
			offsetCanvasX - rotateA * scale * centerX - rotateC * scale * centerY,
			offsetCanvasY - rotateB * scale * centerX - rotateD * scale * centerY
		];
		this.width = width;
		this.height = height;
	}
	get rawDims() {
		const { userUnit, viewBox } = this;
		const dims = viewBox.map((x) => x * userUnit);
		return shadow$1(this, "rawDims", {
			pageWidth: dims[2] - dims[0],
			pageHeight: dims[3] - dims[1],
			pageX: dims[0],
			pageY: dims[1]
		});
	}
	clone({ scale = this.scale, rotation = this.rotation, offsetX = this.offsetX, offsetY = this.offsetY, dontFlip = false } = {}) {
		return new PageViewport({
			viewBox: this.viewBox.slice(),
			userUnit: this.userUnit,
			scale,
			rotation,
			offsetX,
			offsetY,
			dontFlip
		});
	}
	convertToViewportPoint(x, y) {
		return Util$1.applyTransform([x, y], this.transform);
	}
	convertToViewportRectangle(rect) {
		const topLeft = Util$1.applyTransform([rect[0], rect[1]], this.transform);
		const bottomRight = Util$1.applyTransform([rect[2], rect[3]], this.transform);
		return [
			topLeft[0],
			topLeft[1],
			bottomRight[0],
			bottomRight[1]
		];
	}
	convertToPdfPoint(x, y) {
		return Util$1.applyInverseTransform([x, y], this.transform);
	}
};
var RenderingCancelledException$1 = class extends BaseException {
	constructor(msg, extraDelay = 0) {
		super(msg, "RenderingCancelledException");
		this.extraDelay = extraDelay;
	}
};
function isDataScheme$1(url) {
	const ii = url.length;
	let i = 0;
	while (i < ii && url[i].trim() === "") i++;
	return url.substring(i, i + 5).toLowerCase() === "data:";
}
function isPdfFile$1(filename) {
	return typeof filename === "string" && /\.pdf$/i.test(filename);
}
function getFilenameFromUrl$1(url) {
	[url] = url.split(/[#?]/, 1);
	return url.substring(url.lastIndexOf("/") + 1);
}
function getPdfFilenameFromUrl$1(url, defaultFilename = "document.pdf") {
	if (typeof url !== "string") return defaultFilename;
	if (isDataScheme$1(url)) {
		warn("getPdfFilenameFromUrl: ignore \"data:\"-URL for performance reasons.");
		return defaultFilename;
	}
	const reURI = /^(?:(?:[^:]+:)?\/\/[^/]+)?([^?#]*)(\?[^#]*)?(#.*)?$/;
	const reFilename = /[^/?#=]+\.pdf\b(?!.*\.pdf\b)/i;
	const splitURI = reURI.exec(url);
	let suggestedFilename = reFilename.exec(splitURI[1]) || reFilename.exec(splitURI[2]) || reFilename.exec(splitURI[3]);
	if (suggestedFilename) {
		suggestedFilename = suggestedFilename[0];
		if (suggestedFilename.includes("%")) try {
			suggestedFilename = reFilename.exec(decodeURIComponent(suggestedFilename))[0];
		} catch {}
	}
	return suggestedFilename || defaultFilename;
}
var StatTimer = class {
	started = Object.create(null);
	times = [];
	time(name) {
		if (name in this.started) warn(`Timer is already running for ${name}`);
		this.started[name] = Date.now();
	}
	timeEnd(name) {
		if (!(name in this.started)) warn(`Timer has not been started for ${name}`);
		this.times.push({
			name,
			start: this.started[name],
			end: Date.now()
		});
		delete this.started[name];
	}
	toString() {
		const outBuf = [];
		let longest = 0;
		for (const { name } of this.times) longest = Math.max(name.length, longest);
		for (const { name, start, end } of this.times) outBuf.push(`${name.padEnd(longest)} ${end - start}ms\n`);
		return outBuf.join("");
	}
};
function isValidFetchUrl(url, baseUrl) {
	try {
		const { protocol } = baseUrl ? new URL(url, baseUrl) : new URL(url);
		return protocol === "http:" || protocol === "https:";
	} catch {
		return false;
	}
}
function noContextMenu$1(e) {
	e.preventDefault();
}
function stopEvent$1(e) {
	e.preventDefault();
	e.stopPropagation();
}
var PDFDateString$1 = class {
	static #regex;
	static toDateObject(input) {
		if (!input || typeof input !== "string") return null;
		this.#regex ||= /* @__PURE__ */ new RegExp("^D:(\\d{4})(\\d{2})?(\\d{2})?(\\d{2})?(\\d{2})?(\\d{2})?([Z|+|-])?(\\d{2})?'?(\\d{2})?'?");
		const matches = this.#regex.exec(input);
		if (!matches) return null;
		const year = parseInt(matches[1], 10);
		let month = parseInt(matches[2], 10);
		month = month >= 1 && month <= 12 ? month - 1 : 0;
		let day = parseInt(matches[3], 10);
		day = day >= 1 && day <= 31 ? day : 1;
		let hour = parseInt(matches[4], 10);
		hour = hour >= 0 && hour <= 23 ? hour : 0;
		let minute = parseInt(matches[5], 10);
		minute = minute >= 0 && minute <= 59 ? minute : 0;
		let second = parseInt(matches[6], 10);
		second = second >= 0 && second <= 59 ? second : 0;
		const universalTimeRelation = matches[7] || "Z";
		let offsetHour = parseInt(matches[8], 10);
		offsetHour = offsetHour >= 0 && offsetHour <= 23 ? offsetHour : 0;
		let offsetMinute = parseInt(matches[9], 10) || 0;
		offsetMinute = offsetMinute >= 0 && offsetMinute <= 59 ? offsetMinute : 0;
		if (universalTimeRelation === "-") {
			hour += offsetHour;
			minute += offsetMinute;
		} else if (universalTimeRelation === "+") {
			hour -= offsetHour;
			minute -= offsetMinute;
		}
		return new Date(Date.UTC(year, month, day, hour, minute, second));
	}
};
function getXfaPageViewport$1(xfaPage, { scale = 1, rotation = 0 }) {
	const { width, height } = xfaPage.attributes.style;
	return new PageViewport({
		viewBox: [
			0,
			0,
			parseInt(width),
			parseInt(height)
		],
		userUnit: 1,
		scale,
		rotation
	});
}
function getRGB(color) {
	if (color.startsWith("#")) {
		const colorRGB = parseInt(color.slice(1), 16);
		return [
			(colorRGB & 16711680) >> 16,
			(colorRGB & 65280) >> 8,
			colorRGB & 255
		];
	}
	if (color.startsWith("rgb(")) return color.slice(4, -1).split(",").map((x) => parseInt(x));
	if (color.startsWith("rgba(")) return color.slice(5, -1).split(",").map((x) => parseInt(x)).slice(0, 3);
	warn(`Not a valid color format: "${color}"`);
	return [
		0,
		0,
		0
	];
}
function getColorValues(colors) {
	const span = document.createElement("span");
	span.style.visibility = "hidden";
	document.body.append(span);
	for (const name of colors.keys()) {
		span.style.color = name;
		const computedColor = window.getComputedStyle(span).color;
		colors.set(name, getRGB(computedColor));
	}
	span.remove();
}
function getCurrentTransform(ctx) {
	const { a, b, c, d, e, f } = ctx.getTransform();
	return [
		a,
		b,
		c,
		d,
		e,
		f
	];
}
function getCurrentTransformInverse(ctx) {
	const { a, b, c, d, e, f } = ctx.getTransform().invertSelf();
	return [
		a,
		b,
		c,
		d,
		e,
		f
	];
}
function setLayerDimensions$1(div, viewport, mustFlip = false, mustRotate = true) {
	if (viewport instanceof PageViewport) {
		const { pageWidth, pageHeight } = viewport.rawDims;
		const { style } = div;
		const useRound = util_FeatureTest.isCSSRoundSupported;
		const w = `var(--scale-factor) * ${pageWidth}px`, h = `var(--scale-factor) * ${pageHeight}px`;
		const widthStr = useRound ? `round(down, ${w}, var(--scale-round-x, 1px))` : `calc(${w})`, heightStr = useRound ? `round(down, ${h}, var(--scale-round-y, 1px))` : `calc(${h})`;
		if (!mustFlip || viewport.rotation % 180 === 0) {
			style.width = widthStr;
			style.height = heightStr;
		} else {
			style.width = heightStr;
			style.height = widthStr;
		}
	}
	if (mustRotate) div.setAttribute("data-main-rotation", viewport.rotation);
}
var OutputScale$1 = class {
	constructor() {
		const pixelRatio = window.devicePixelRatio || 1;
		this.sx = pixelRatio;
		this.sy = pixelRatio;
	}
	get scaled() {
		return this.sx !== 1 || this.sy !== 1;
	}
	get symmetric() {
		return this.sx === this.sy;
	}
};
var EditorToolbar = class EditorToolbar {
	#toolbar = null;
	#colorPicker = null;
	#editor;
	#buttons = null;
	#altText = null;
	static #l10nRemove = null;
	constructor(editor) {
		this.#editor = editor;
		EditorToolbar.#l10nRemove ||= Object.freeze({
			freetext: "pdfjs-editor-remove-freetext-button",
			highlight: "pdfjs-editor-remove-highlight-button",
			ink: "pdfjs-editor-remove-ink-button",
			stamp: "pdfjs-editor-remove-stamp-button"
		});
	}
	render() {
		const editToolbar = this.#toolbar = document.createElement("div");
		editToolbar.classList.add("editToolbar", "hidden");
		editToolbar.setAttribute("role", "toolbar");
		const signal = this.#editor._uiManager._signal;
		editToolbar.addEventListener("contextmenu", noContextMenu$1, { signal });
		editToolbar.addEventListener("pointerdown", EditorToolbar.#pointerDown, { signal });
		const buttons = this.#buttons = document.createElement("div");
		buttons.className = "buttons";
		editToolbar.append(buttons);
		const position = this.#editor.toolbarPosition;
		if (position) {
			const { style } = editToolbar;
			style.insetInlineEnd = `${100 * (this.#editor._uiManager.direction === "ltr" ? 1 - position[0] : position[0])}%`;
			style.top = `calc(${100 * position[1]}% + var(--editor-toolbar-vert-offset))`;
		}
		this.#addDeleteButton();
		return editToolbar;
	}
	get div() {
		return this.#toolbar;
	}
	static #pointerDown(e) {
		e.stopPropagation();
	}
	#focusIn(e) {
		this.#editor._focusEventsAllowed = false;
		stopEvent$1(e);
	}
	#focusOut(e) {
		this.#editor._focusEventsAllowed = true;
		stopEvent$1(e);
	}
	#addListenersToElement(element) {
		const signal = this.#editor._uiManager._signal;
		element.addEventListener("focusin", this.#focusIn.bind(this), {
			capture: true,
			signal
		});
		element.addEventListener("focusout", this.#focusOut.bind(this), {
			capture: true,
			signal
		});
		element.addEventListener("contextmenu", noContextMenu$1, { signal });
	}
	hide() {
		this.#toolbar.classList.add("hidden");
		this.#colorPicker?.hideDropdown();
	}
	show() {
		this.#toolbar.classList.remove("hidden");
		this.#altText?.shown();
	}
	#addDeleteButton() {
		const { editorType, _uiManager } = this.#editor;
		const button = document.createElement("button");
		button.className = "delete";
		button.tabIndex = 0;
		button.setAttribute("data-l10n-id", EditorToolbar.#l10nRemove[editorType]);
		this.#addListenersToElement(button);
		button.addEventListener("click", (e) => {
			_uiManager.delete();
		}, { signal: _uiManager._signal });
		this.#buttons.append(button);
	}
	get #divider() {
		const divider = document.createElement("div");
		divider.className = "divider";
		return divider;
	}
	async addAltText(altText) {
		const button = await altText.render();
		this.#addListenersToElement(button);
		this.#buttons.prepend(button, this.#divider);
		this.#altText = altText;
	}
	addColorPicker(colorPicker) {
		this.#colorPicker = colorPicker;
		const button = colorPicker.renderButton();
		this.#addListenersToElement(button);
		this.#buttons.prepend(button, this.#divider);
	}
	remove() {
		this.#toolbar.remove();
		this.#colorPicker?.destroy();
		this.#colorPicker = null;
	}
};
var HighlightToolbar = class {
	#buttons = null;
	#toolbar = null;
	#uiManager;
	constructor(uiManager) {
		this.#uiManager = uiManager;
	}
	#render() {
		const editToolbar = this.#toolbar = document.createElement("div");
		editToolbar.className = "editToolbar";
		editToolbar.setAttribute("role", "toolbar");
		editToolbar.addEventListener("contextmenu", noContextMenu$1, { signal: this.#uiManager._signal });
		const buttons = this.#buttons = document.createElement("div");
		buttons.className = "buttons";
		editToolbar.append(buttons);
		this.#addHighlightButton();
		return editToolbar;
	}
	#getLastPoint(boxes, isLTR) {
		let lastY = 0;
		let lastX = 0;
		for (const box of boxes) {
			const y = box.y + box.height;
			if (y < lastY) continue;
			const x = box.x + (isLTR ? box.width : 0);
			if (y > lastY) {
				lastX = x;
				lastY = y;
				continue;
			}
			if (isLTR) {
				if (x > lastX) lastX = x;
			} else if (x < lastX) lastX = x;
		}
		return [isLTR ? 1 - lastX : lastX, lastY];
	}
	show(parent, boxes, isLTR) {
		const [x, y] = this.#getLastPoint(boxes, isLTR);
		const { style } = this.#toolbar ||= this.#render();
		parent.append(this.#toolbar);
		style.insetInlineEnd = `${100 * x}%`;
		style.top = `calc(${100 * y}% + var(--editor-toolbar-vert-offset))`;
	}
	hide() {
		this.#toolbar.remove();
	}
	#addHighlightButton() {
		const button = document.createElement("button");
		button.className = "highlightButton";
		button.tabIndex = 0;
		button.setAttribute("data-l10n-id", `pdfjs-highlight-floating-button1`);
		const span = document.createElement("span");
		button.append(span);
		span.className = "visuallyHidden";
		span.setAttribute("data-l10n-id", "pdfjs-highlight-floating-button-label");
		const signal = this.#uiManager._signal;
		button.addEventListener("contextmenu", noContextMenu$1, { signal });
		button.addEventListener("click", () => {
			this.#uiManager.highlightSelection("floating_button");
		}, { signal });
		this.#buttons.append(button);
	}
};
function bindEvents(obj, element, names) {
	for (const name of names) element.addEventListener(name, obj[name].bind(obj));
}
var IdManager = class {
	#id = 0;
	get id() {
		return `${AnnotationEditorPrefix}${this.#id++}`;
	}
};
var ImageManager = class ImageManager {
	#baseId = getUuid();
	#id = 0;
	#cache = null;
	static get _isSVGFittingCanvas() {
		const svg = `data:image/svg+xml;charset=UTF-8,<svg viewBox="0 0 1 1" width="1" height="1" xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1" style="fill:red;"/></svg>`;
		const ctx = new OffscreenCanvas(1, 3).getContext("2d", { willReadFrequently: true });
		const image = new Image();
		image.src = svg;
		const promise = image.decode().then(() => {
			ctx.drawImage(image, 0, 0, 1, 1, 0, 0, 1, 3);
			return new Uint32Array(ctx.getImageData(0, 0, 1, 1).data.buffer)[0] === 0;
		});
		return shadow$1(this, "_isSVGFittingCanvas", promise);
	}
	async #get(key, rawData) {
		this.#cache ||= /* @__PURE__ */ new Map();
		let data = this.#cache.get(key);
		if (data === null) return null;
		if (data?.bitmap) {
			data.refCounter += 1;
			return data;
		}
		try {
			data ||= {
				bitmap: null,
				id: `image_${this.#baseId}_${this.#id++}`,
				refCounter: 0,
				isSvg: false
			};
			let image;
			if (typeof rawData === "string") {
				data.url = rawData;
				image = await fetchData$1(rawData, "blob");
			} else if (rawData instanceof File) image = data.file = rawData;
			else if (rawData instanceof Blob) image = rawData;
			if (image.type === "image/svg+xml") {
				const mustRemoveAspectRatioPromise = ImageManager._isSVGFittingCanvas;
				const fileReader = new FileReader();
				const imageElement = new Image();
				const imagePromise = new Promise((resolve, reject) => {
					imageElement.onload = () => {
						data.bitmap = imageElement;
						data.isSvg = true;
						resolve();
					};
					fileReader.onload = async () => {
						const url = data.svgUrl = fileReader.result;
						imageElement.src = await mustRemoveAspectRatioPromise ? `${url}#svgView(preserveAspectRatio(none))` : url;
					};
					imageElement.onerror = fileReader.onerror = reject;
				});
				fileReader.readAsDataURL(image);
				await imagePromise;
			} else data.bitmap = await createImageBitmap(image);
			data.refCounter = 1;
		} catch (e) {
			warn(e);
			data = null;
		}
		this.#cache.set(key, data);
		if (data) this.#cache.set(data.id, data);
		return data;
	}
	async getFromFile(file) {
		const { lastModified, name, size, type } = file;
		return this.#get(`${lastModified}_${name}_${size}_${type}`, file);
	}
	async getFromUrl(url) {
		return this.#get(url, url);
	}
	async getFromBlob(id, blobPromise) {
		const blob = await blobPromise;
		return this.#get(id, blob);
	}
	async getFromId(id) {
		this.#cache ||= /* @__PURE__ */ new Map();
		const data = this.#cache.get(id);
		if (!data) return null;
		if (data.bitmap) {
			data.refCounter += 1;
			return data;
		}
		if (data.file) return this.getFromFile(data.file);
		if (data.blobPromise) {
			const { blobPromise } = data;
			delete data.blobPromise;
			return this.getFromBlob(data.id, blobPromise);
		}
		return this.getFromUrl(data.url);
	}
	getFromCanvas(id, canvas) {
		this.#cache ||= /* @__PURE__ */ new Map();
		let data = this.#cache.get(id);
		if (data?.bitmap) {
			data.refCounter += 1;
			return data;
		}
		const offscreen = new OffscreenCanvas(canvas.width, canvas.height);
		offscreen.getContext("2d").drawImage(canvas, 0, 0);
		data = {
			bitmap: offscreen.transferToImageBitmap(),
			id: `image_${this.#baseId}_${this.#id++}`,
			refCounter: 1,
			isSvg: false
		};
		this.#cache.set(id, data);
		this.#cache.set(data.id, data);
		return data;
	}
	getSvgUrl(id) {
		const data = this.#cache.get(id);
		if (!data?.isSvg) return null;
		return data.svgUrl;
	}
	deleteId(id) {
		this.#cache ||= /* @__PURE__ */ new Map();
		const data = this.#cache.get(id);
		if (!data) return;
		data.refCounter -= 1;
		if (data.refCounter !== 0) return;
		const { bitmap } = data;
		if (!data.url && !data.file) {
			const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
			canvas.getContext("bitmaprenderer").transferFromImageBitmap(bitmap);
			data.blobPromise = canvas.convertToBlob();
		}
		bitmap.close?.();
		data.bitmap = null;
	}
	isValidId(id) {
		return id.startsWith(`image_${this.#baseId}_`);
	}
};
var CommandManager = class {
	#commands = [];
	#locked = false;
	#maxSize;
	#position = -1;
	constructor(maxSize = 128) {
		this.#maxSize = maxSize;
	}
	add({ cmd, undo, post, mustExec, type = NaN, overwriteIfSameType = false, keepUndo = false }) {
		if (mustExec) cmd();
		if (this.#locked) return;
		const save = {
			cmd,
			undo,
			post,
			type
		};
		if (this.#position === -1) {
			if (this.#commands.length > 0) this.#commands.length = 0;
			this.#position = 0;
			this.#commands.push(save);
			return;
		}
		if (overwriteIfSameType && this.#commands[this.#position].type === type) {
			if (keepUndo) save.undo = this.#commands[this.#position].undo;
			this.#commands[this.#position] = save;
			return;
		}
		const next = this.#position + 1;
		if (next === this.#maxSize) this.#commands.splice(0, 1);
		else {
			this.#position = next;
			if (next < this.#commands.length) this.#commands.splice(next);
		}
		this.#commands.push(save);
	}
	undo() {
		if (this.#position === -1) return;
		this.#locked = true;
		const { undo, post } = this.#commands[this.#position];
		undo();
		post?.();
		this.#locked = false;
		this.#position -= 1;
	}
	redo() {
		if (this.#position < this.#commands.length - 1) {
			this.#position += 1;
			this.#locked = true;
			const { cmd, post } = this.#commands[this.#position];
			cmd();
			post?.();
			this.#locked = false;
		}
	}
	hasSomethingToUndo() {
		return this.#position !== -1;
	}
	hasSomethingToRedo() {
		return this.#position < this.#commands.length - 1;
	}
	cleanType(type) {
		if (this.#position === -1) return;
		for (let i = this.#position; i >= 0; i--) if (this.#commands[i].type !== type) {
			this.#commands.splice(i + 1, this.#position - i);
			this.#position = i;
			return;
		}
		this.#commands.length = 0;
		this.#position = -1;
	}
	destroy() {
		this.#commands = null;
	}
};
var KeyboardManager = class {
	constructor(callbacks) {
		this.buffer = [];
		this.callbacks = /* @__PURE__ */ new Map();
		this.allKeys = /* @__PURE__ */ new Set();
		const { isMac } = util_FeatureTest.platform;
		for (const [keys, callback, options = {}] of callbacks) for (const key of keys) {
			const isMacKey = key.startsWith("mac+");
			if (isMac && isMacKey) {
				this.callbacks.set(key.slice(4), {
					callback,
					options
				});
				this.allKeys.add(key.split("+").at(-1));
			} else if (!isMac && !isMacKey) {
				this.callbacks.set(key, {
					callback,
					options
				});
				this.allKeys.add(key.split("+").at(-1));
			}
		}
	}
	#serialize(event) {
		if (event.altKey) this.buffer.push("alt");
		if (event.ctrlKey) this.buffer.push("ctrl");
		if (event.metaKey) this.buffer.push("meta");
		if (event.shiftKey) this.buffer.push("shift");
		this.buffer.push(event.key);
		const str = this.buffer.join("+");
		this.buffer.length = 0;
		return str;
	}
	exec(self, event) {
		if (!this.allKeys.has(event.key)) return;
		const info = this.callbacks.get(this.#serialize(event));
		if (!info) return;
		const { callback, options: { bubbles = false, args = [], checker = null } } = info;
		if (checker && !checker(self, event)) return;
		callback.bind(self, ...args, event)();
		if (!bubbles) stopEvent$1(event);
	}
};
var ColorManager = class ColorManager {
	static _colorsMapping = /* @__PURE__ */ new Map([["CanvasText", [
		0,
		0,
		0
	]], ["Canvas", [
		255,
		255,
		255
	]]]);
	get _colors() {
		const colors = /* @__PURE__ */ new Map([["CanvasText", null], ["Canvas", null]]);
		getColorValues(colors);
		return shadow$1(this, "_colors", colors);
	}
	convert(color) {
		const rgb = getRGB(color);
		if (!window.matchMedia("(forced-colors: active)").matches) return rgb;
		for (const [name, RGB] of this._colors) if (RGB.every((x, i) => x === rgb[i])) return ColorManager._colorsMapping.get(name);
		return rgb;
	}
	getHexCode(name) {
		const rgb = this._colors.get(name);
		if (!rgb) return name;
		return Util$1.makeHexColor(...rgb);
	}
};
var AnnotationEditorUIManager$1 = class AnnotationEditorUIManager$1 {
	#abortController = new AbortController();
	#activeEditor = null;
	#allEditors = /* @__PURE__ */ new Map();
	#allLayers = /* @__PURE__ */ new Map();
	#altTextManager = null;
	#annotationStorage = null;
	#changedExistingAnnotations = null;
	#commandManager = new CommandManager();
	#copyPasteAC = null;
	#currentDrawingSession = null;
	#currentPageIndex = 0;
	#deletedAnnotationsElementIds = /* @__PURE__ */ new Set();
	#draggingEditors = null;
	#editorTypes = null;
	#editorsToRescale = /* @__PURE__ */ new Set();
	_editorUndoBar = null;
	#enableHighlightFloatingButton = false;
	#enableUpdatedAddImage = false;
	#enableNewAltTextWhenAddingImage = false;
	#filterFactory = null;
	#focusMainContainerTimeoutId = null;
	#focusManagerAC = null;
	#highlightColors = null;
	#highlightWhenShiftUp = false;
	#highlightToolbar = null;
	#idManager = new IdManager();
	#isEnabled = false;
	#isWaiting = false;
	#keyboardManagerAC = null;
	#lastActiveElement = null;
	#mainHighlightColorPicker = null;
	#mlManager = null;
	#mode = AnnotationEditorType$1.NONE;
	#selectedEditors = /* @__PURE__ */ new Set();
	#selectedTextNode = null;
	#pageColors = null;
	#showAllStates = null;
	#previousStates = {
		isEditing: false,
		isEmpty: true,
		hasSomethingToUndo: false,
		hasSomethingToRedo: false,
		hasSelectedEditor: false,
		hasSelectedText: false
	};
	#translation = [0, 0];
	#translationTimeoutId = null;
	#container = null;
	#viewer = null;
	#updateModeCapability = null;
	static TRANSLATE_SMALL = 1;
	static TRANSLATE_BIG = 10;
	static get _keyboardManager() {
		const proto = AnnotationEditorUIManager$1.prototype;
		const arrowChecker = (self) => self.#container.contains(document.activeElement) && document.activeElement.tagName !== "BUTTON" && self.hasSomethingToControl();
		const textInputChecker = (_self, { target: el }) => {
			if (el instanceof HTMLInputElement) {
				const { type } = el;
				return type !== "text" && type !== "number";
			}
			return true;
		};
		const small = this.TRANSLATE_SMALL;
		const big = this.TRANSLATE_BIG;
		return shadow$1(this, "_keyboardManager", new KeyboardManager([
			[
				["ctrl+a", "mac+meta+a"],
				proto.selectAll,
				{ checker: textInputChecker }
			],
			[
				["ctrl+z", "mac+meta+z"],
				proto.undo,
				{ checker: textInputChecker }
			],
			[
				[
					"ctrl+y",
					"ctrl+shift+z",
					"mac+meta+shift+z",
					"ctrl+shift+Z",
					"mac+meta+shift+Z"
				],
				proto.redo,
				{ checker: textInputChecker }
			],
			[
				[
					"Backspace",
					"alt+Backspace",
					"ctrl+Backspace",
					"shift+Backspace",
					"mac+Backspace",
					"mac+alt+Backspace",
					"mac+ctrl+Backspace",
					"Delete",
					"ctrl+Delete",
					"shift+Delete",
					"mac+Delete"
				],
				proto.delete,
				{ checker: textInputChecker }
			],
			[
				["Enter", "mac+Enter"],
				proto.addNewEditorFromKeyboard,
				{ checker: (self, { target: el }) => !(el instanceof HTMLButtonElement) && self.#container.contains(el) && !self.isEnterHandled }
			],
			[
				[" ", "mac+ "],
				proto.addNewEditorFromKeyboard,
				{ checker: (self, { target: el }) => !(el instanceof HTMLButtonElement) && self.#container.contains(document.activeElement) }
			],
			[["Escape", "mac+Escape"], proto.unselectAll],
			[
				["ArrowLeft", "mac+ArrowLeft"],
				proto.translateSelectedEditors,
				{
					args: [-small, 0],
					checker: arrowChecker
				}
			],
			[
				["ctrl+ArrowLeft", "mac+shift+ArrowLeft"],
				proto.translateSelectedEditors,
				{
					args: [-big, 0],
					checker: arrowChecker
				}
			],
			[
				["ArrowRight", "mac+ArrowRight"],
				proto.translateSelectedEditors,
				{
					args: [small, 0],
					checker: arrowChecker
				}
			],
			[
				["ctrl+ArrowRight", "mac+shift+ArrowRight"],
				proto.translateSelectedEditors,
				{
					args: [big, 0],
					checker: arrowChecker
				}
			],
			[
				["ArrowUp", "mac+ArrowUp"],
				proto.translateSelectedEditors,
				{
					args: [0, -small],
					checker: arrowChecker
				}
			],
			[
				["ctrl+ArrowUp", "mac+shift+ArrowUp"],
				proto.translateSelectedEditors,
				{
					args: [0, -big],
					checker: arrowChecker
				}
			],
			[
				["ArrowDown", "mac+ArrowDown"],
				proto.translateSelectedEditors,
				{
					args: [0, small],
					checker: arrowChecker
				}
			],
			[
				["ctrl+ArrowDown", "mac+shift+ArrowDown"],
				proto.translateSelectedEditors,
				{
					args: [0, big],
					checker: arrowChecker
				}
			]
		]));
	}
	constructor(container, viewer, altTextManager, eventBus, pdfDocument, pageColors, highlightColors, enableHighlightFloatingButton, enableUpdatedAddImage, enableNewAltTextWhenAddingImage, mlManager, editorUndoBar, supportsPinchToZoom) {
		const signal = this._signal = this.#abortController.signal;
		this.#container = container;
		this.#viewer = viewer;
		this.#altTextManager = altTextManager;
		this._eventBus = eventBus;
		eventBus._on("editingaction", this.onEditingAction.bind(this), { signal });
		eventBus._on("pagechanging", this.onPageChanging.bind(this), { signal });
		eventBus._on("scalechanging", this.onScaleChanging.bind(this), { signal });
		eventBus._on("rotationchanging", this.onRotationChanging.bind(this), { signal });
		eventBus._on("setpreference", this.onSetPreference.bind(this), { signal });
		eventBus._on("switchannotationeditorparams", (evt) => this.updateParams(evt.type, evt.value), { signal });
		this.#addSelectionListener();
		this.#addDragAndDropListeners();
		this.#addKeyboardManager();
		this.#annotationStorage = pdfDocument.annotationStorage;
		this.#filterFactory = pdfDocument.filterFactory;
		this.#pageColors = pageColors;
		this.#highlightColors = highlightColors || null;
		this.#enableHighlightFloatingButton = enableHighlightFloatingButton;
		this.#enableUpdatedAddImage = enableUpdatedAddImage;
		this.#enableNewAltTextWhenAddingImage = enableNewAltTextWhenAddingImage;
		this.#mlManager = mlManager || null;
		this.viewParameters = {
			realScale: PixelsPerInch$1.PDF_TO_CSS_UNITS,
			rotation: 0
		};
		this.isShiftKeyDown = false;
		this._editorUndoBar = editorUndoBar || null;
		this._supportsPinchToZoom = supportsPinchToZoom !== false;
	}
	destroy() {
		this.#updateModeCapability?.resolve();
		this.#updateModeCapability = null;
		this.#abortController?.abort();
		this.#abortController = null;
		this._signal = null;
		for (const layer of this.#allLayers.values()) layer.destroy();
		this.#allLayers.clear();
		this.#allEditors.clear();
		this.#editorsToRescale.clear();
		this.#activeEditor = null;
		this.#selectedEditors.clear();
		this.#commandManager.destroy();
		this.#altTextManager?.destroy();
		this.#highlightToolbar?.hide();
		this.#highlightToolbar = null;
		if (this.#focusMainContainerTimeoutId) {
			clearTimeout(this.#focusMainContainerTimeoutId);
			this.#focusMainContainerTimeoutId = null;
		}
		if (this.#translationTimeoutId) {
			clearTimeout(this.#translationTimeoutId);
			this.#translationTimeoutId = null;
		}
		this._editorUndoBar?.destroy();
	}
	combinedSignal(ac) {
		return AbortSignal.any([this._signal, ac.signal]);
	}
	get mlManager() {
		return this.#mlManager;
	}
	get useNewAltTextFlow() {
		return this.#enableUpdatedAddImage;
	}
	get useNewAltTextWhenAddingImage() {
		return this.#enableNewAltTextWhenAddingImage;
	}
	get hcmFilter() {
		return shadow$1(this, "hcmFilter", this.#pageColors ? this.#filterFactory.addHCMFilter(this.#pageColors.foreground, this.#pageColors.background) : "none");
	}
	get direction() {
		return shadow$1(this, "direction", getComputedStyle(this.#container).direction);
	}
	get highlightColors() {
		return shadow$1(this, "highlightColors", this.#highlightColors ? new Map(this.#highlightColors.split(",").map((pair) => pair.split("=").map((x) => x.trim()))) : null);
	}
	get highlightColorNames() {
		return shadow$1(this, "highlightColorNames", this.highlightColors ? new Map(Array.from(this.highlightColors, (e) => e.reverse())) : null);
	}
	setCurrentDrawingSession(layer) {
		if (layer) {
			this.unselectAll();
			this.disableUserSelect(true);
		} else this.disableUserSelect(false);
		this.#currentDrawingSession = layer;
	}
	setMainHighlightColorPicker(colorPicker) {
		this.#mainHighlightColorPicker = colorPicker;
	}
	editAltText(editor, firstTime = false) {
		this.#altTextManager?.editAltText(this, editor, firstTime);
	}
	switchToMode(mode, callback) {
		this._eventBus.on("annotationeditormodechanged", callback, {
			once: true,
			signal: this._signal
		});
		this._eventBus.dispatch("showannotationeditorui", {
			source: this,
			mode
		});
	}
	setPreference(name, value) {
		this._eventBus.dispatch("setpreference", {
			source: this,
			name,
			value
		});
	}
	onSetPreference({ name, value }) {
		switch (name) {
			case "enableNewAltTextWhenAddingImage": this.#enableNewAltTextWhenAddingImage = value;
		}
	}
	onPageChanging({ pageNumber }) {
		this.#currentPageIndex = pageNumber - 1;
	}
	focusMainContainer() {
		this.#container.focus();
	}
	findParent(x, y) {
		for (const layer of this.#allLayers.values()) {
			const { x: layerX, y: layerY, width, height } = layer.div.getBoundingClientRect();
			if (x >= layerX && x <= layerX + width && y >= layerY && y <= layerY + height) return layer;
		}
		return null;
	}
	disableUserSelect(value = false) {
		this.#viewer.classList.toggle("noUserSelect", value);
	}
	addShouldRescale(editor) {
		this.#editorsToRescale.add(editor);
	}
	removeShouldRescale(editor) {
		this.#editorsToRescale.delete(editor);
	}
	onScaleChanging({ scale }) {
		this.commitOrRemove();
		this.viewParameters.realScale = scale * PixelsPerInch$1.PDF_TO_CSS_UNITS;
		for (const editor of this.#editorsToRescale) editor.onScaleChanging();
		this.#currentDrawingSession?.onScaleChanging();
	}
	onRotationChanging({ pagesRotation }) {
		this.commitOrRemove();
		this.viewParameters.rotation = pagesRotation;
	}
	#getAnchorElementForSelection({ anchorNode }) {
		return anchorNode.nodeType === Node.TEXT_NODE ? anchorNode.parentElement : anchorNode;
	}
	#getLayerForTextLayer(textLayer) {
		const { currentLayer } = this;
		if (currentLayer.hasTextLayer(textLayer)) return currentLayer;
		for (const layer of this.#allLayers.values()) if (layer.hasTextLayer(textLayer)) return layer;
		return null;
	}
	highlightSelection(methodOfCreation = "") {
		const selection = document.getSelection();
		if (!selection || selection.isCollapsed) return;
		const { anchorNode, anchorOffset, focusNode, focusOffset } = selection;
		const text = selection.toString();
		const textLayer = this.#getAnchorElementForSelection(selection).closest(".textLayer");
		const boxes = this.getSelectionBoxes(textLayer);
		if (!boxes) return;
		selection.empty();
		const layer = this.#getLayerForTextLayer(textLayer);
		const isNoneMode = this.#mode === AnnotationEditorType$1.NONE;
		const callback = () => {
			layer?.createAndAddNewEditor({
				x: 0,
				y: 0
			}, false, {
				methodOfCreation,
				boxes,
				anchorNode,
				anchorOffset,
				focusNode,
				focusOffset,
				text
			});
			if (isNoneMode) this.showAllEditors("highlight", true, true);
		};
		if (isNoneMode) {
			this.switchToMode(AnnotationEditorType$1.HIGHLIGHT, callback);
			return;
		}
		callback();
	}
	#displayHighlightToolbar() {
		const selection = document.getSelection();
		if (!selection || selection.isCollapsed) return;
		const textLayer = this.#getAnchorElementForSelection(selection).closest(".textLayer");
		const boxes = this.getSelectionBoxes(textLayer);
		if (!boxes) return;
		this.#highlightToolbar ||= new HighlightToolbar(this);
		this.#highlightToolbar.show(textLayer, boxes, this.direction === "ltr");
	}
	addToAnnotationStorage(editor) {
		if (!editor.isEmpty() && this.#annotationStorage && !this.#annotationStorage.has(editor.id)) this.#annotationStorage.setValue(editor.id, editor);
	}
	#selectionChange() {
		const selection = document.getSelection();
		if (!selection || selection.isCollapsed) {
			if (this.#selectedTextNode) {
				this.#highlightToolbar?.hide();
				this.#selectedTextNode = null;
				this.#dispatchUpdateStates({ hasSelectedText: false });
			}
			return;
		}
		const { anchorNode } = selection;
		if (anchorNode === this.#selectedTextNode) return;
		const textLayer = this.#getAnchorElementForSelection(selection).closest(".textLayer");
		if (!textLayer) {
			if (this.#selectedTextNode) {
				this.#highlightToolbar?.hide();
				this.#selectedTextNode = null;
				this.#dispatchUpdateStates({ hasSelectedText: false });
			}
			return;
		}
		this.#highlightToolbar?.hide();
		this.#selectedTextNode = anchorNode;
		this.#dispatchUpdateStates({ hasSelectedText: true });
		if (this.#mode !== AnnotationEditorType$1.HIGHLIGHT && this.#mode !== AnnotationEditorType$1.NONE) return;
		if (this.#mode === AnnotationEditorType$1.HIGHLIGHT) this.showAllEditors("highlight", true, true);
		this.#highlightWhenShiftUp = this.isShiftKeyDown;
		if (!this.isShiftKeyDown) {
			const activeLayer = this.#mode === AnnotationEditorType$1.HIGHLIGHT ? this.#getLayerForTextLayer(textLayer) : null;
			activeLayer?.toggleDrawing();
			const ac = new AbortController();
			const signal = this.combinedSignal(ac);
			const pointerup = (e) => {
				if (e.type === "pointerup" && e.button !== 0) return;
				ac.abort();
				activeLayer?.toggleDrawing(true);
				if (e.type === "pointerup") this.#onSelectEnd("main_toolbar");
			};
			window.addEventListener("pointerup", pointerup, { signal });
			window.addEventListener("blur", pointerup, { signal });
		}
	}
	#onSelectEnd(methodOfCreation = "") {
		if (this.#mode === AnnotationEditorType$1.HIGHLIGHT) this.highlightSelection(methodOfCreation);
		else if (this.#enableHighlightFloatingButton) this.#displayHighlightToolbar();
	}
	#addSelectionListener() {
		document.addEventListener("selectionchange", this.#selectionChange.bind(this), { signal: this._signal });
	}
	#addFocusManager() {
		if (this.#focusManagerAC) return;
		this.#focusManagerAC = new AbortController();
		const signal = this.combinedSignal(this.#focusManagerAC);
		window.addEventListener("focus", this.focus.bind(this), { signal });
		window.addEventListener("blur", this.blur.bind(this), { signal });
	}
	#removeFocusManager() {
		this.#focusManagerAC?.abort();
		this.#focusManagerAC = null;
	}
	blur() {
		this.isShiftKeyDown = false;
		if (this.#highlightWhenShiftUp) {
			this.#highlightWhenShiftUp = false;
			this.#onSelectEnd("main_toolbar");
		}
		if (!this.hasSelection) return;
		const { activeElement } = document;
		for (const editor of this.#selectedEditors) if (editor.div.contains(activeElement)) {
			this.#lastActiveElement = [editor, activeElement];
			editor._focusEventsAllowed = false;
			break;
		}
	}
	focus() {
		if (!this.#lastActiveElement) return;
		const [lastEditor, lastActiveElement] = this.#lastActiveElement;
		this.#lastActiveElement = null;
		lastActiveElement.addEventListener("focusin", () => {
			lastEditor._focusEventsAllowed = true;
		}, {
			once: true,
			signal: this._signal
		});
		lastActiveElement.focus();
	}
	#addKeyboardManager() {
		if (this.#keyboardManagerAC) return;
		this.#keyboardManagerAC = new AbortController();
		const signal = this.combinedSignal(this.#keyboardManagerAC);
		window.addEventListener("keydown", this.keydown.bind(this), { signal });
		window.addEventListener("keyup", this.keyup.bind(this), { signal });
	}
	#removeKeyboardManager() {
		this.#keyboardManagerAC?.abort();
		this.#keyboardManagerAC = null;
	}
	#addCopyPasteListeners() {
		if (this.#copyPasteAC) return;
		this.#copyPasteAC = new AbortController();
		const signal = this.combinedSignal(this.#copyPasteAC);
		document.addEventListener("copy", this.copy.bind(this), { signal });
		document.addEventListener("cut", this.cut.bind(this), { signal });
		document.addEventListener("paste", this.paste.bind(this), { signal });
	}
	#removeCopyPasteListeners() {
		this.#copyPasteAC?.abort();
		this.#copyPasteAC = null;
	}
	#addDragAndDropListeners() {
		const signal = this._signal;
		document.addEventListener("dragover", this.dragOver.bind(this), { signal });
		document.addEventListener("drop", this.drop.bind(this), { signal });
	}
	addEditListeners() {
		this.#addKeyboardManager();
		this.#addCopyPasteListeners();
	}
	removeEditListeners() {
		this.#removeKeyboardManager();
		this.#removeCopyPasteListeners();
	}
	dragOver(event) {
		for (const { type } of event.dataTransfer.items) for (const editorType of this.#editorTypes) if (editorType.isHandlingMimeForPasting(type)) {
			event.dataTransfer.dropEffect = "copy";
			event.preventDefault();
			return;
		}
	}
	drop(event) {
		for (const item of event.dataTransfer.items) for (const editorType of this.#editorTypes) if (editorType.isHandlingMimeForPasting(item.type)) {
			editorType.paste(item, this.currentLayer);
			event.preventDefault();
			return;
		}
	}
	copy(event) {
		event.preventDefault();
		this.#activeEditor?.commitOrRemove();
		if (!this.hasSelection) return;
		const editors = [];
		for (const editor of this.#selectedEditors) {
			const serialized = editor.serialize(true);
			if (serialized) editors.push(serialized);
		}
		if (editors.length === 0) return;
		event.clipboardData.setData("application/pdfjs", JSON.stringify(editors));
	}
	cut(event) {
		this.copy(event);
		this.delete();
	}
	async paste(event) {
		event.preventDefault();
		const { clipboardData } = event;
		for (const item of clipboardData.items) for (const editorType of this.#editorTypes) if (editorType.isHandlingMimeForPasting(item.type)) {
			editorType.paste(item, this.currentLayer);
			return;
		}
		let data = clipboardData.getData("application/pdfjs");
		if (!data) return;
		try {
			data = JSON.parse(data);
		} catch (ex) {
			warn(`paste: "${ex.message}".`);
			return;
		}
		if (!Array.isArray(data)) return;
		this.unselectAll();
		const layer = this.currentLayer;
		try {
			const newEditors = [];
			for (const editor of data) {
				const deserializedEditor = await layer.deserialize(editor);
				if (!deserializedEditor) return;
				newEditors.push(deserializedEditor);
			}
			const cmd = () => {
				for (const editor of newEditors) this.#addEditorToLayer(editor);
				this.#selectEditors(newEditors);
			};
			const undo = () => {
				for (const editor of newEditors) editor.remove();
			};
			this.addCommands({
				cmd,
				undo,
				mustExec: true
			});
		} catch (ex) {
			warn(`paste: "${ex.message}".`);
		}
	}
	keydown(event) {
		if (!this.isShiftKeyDown && event.key === "Shift") this.isShiftKeyDown = true;
		if (this.#mode !== AnnotationEditorType$1.NONE && !this.isEditorHandlingKeyboard) AnnotationEditorUIManager$1._keyboardManager.exec(this, event);
	}
	keyup(event) {
		if (this.isShiftKeyDown && event.key === "Shift") {
			this.isShiftKeyDown = false;
			if (this.#highlightWhenShiftUp) {
				this.#highlightWhenShiftUp = false;
				this.#onSelectEnd("main_toolbar");
			}
		}
	}
	onEditingAction({ name }) {
		switch (name) {
			case "undo":
			case "redo":
			case "delete":
			case "selectAll":
				this[name]();
				break;
			case "highlightSelection": this.highlightSelection("context_menu");
		}
	}
	#dispatchUpdateStates(details) {
		if (Object.entries(details).some(([key, value]) => this.#previousStates[key] !== value)) {
			this._eventBus.dispatch("annotationeditorstateschanged", {
				source: this,
				details: Object.assign(this.#previousStates, details)
			});
			if (this.#mode === AnnotationEditorType$1.HIGHLIGHT && details.hasSelectedEditor === false) this.#dispatchUpdateUI([[AnnotationEditorParamsType$1.HIGHLIGHT_FREE, true]]);
		}
	}
	#dispatchUpdateUI(details) {
		this._eventBus.dispatch("annotationeditorparamschanged", {
			source: this,
			details
		});
	}
	setEditingState(isEditing) {
		if (isEditing) {
			this.#addFocusManager();
			this.#addCopyPasteListeners();
			this.#dispatchUpdateStates({
				isEditing: this.#mode !== AnnotationEditorType$1.NONE,
				isEmpty: this.#isEmpty(),
				hasSomethingToUndo: this.#commandManager.hasSomethingToUndo(),
				hasSomethingToRedo: this.#commandManager.hasSomethingToRedo(),
				hasSelectedEditor: false
			});
		} else {
			this.#removeFocusManager();
			this.#removeCopyPasteListeners();
			this.#dispatchUpdateStates({ isEditing: false });
			this.disableUserSelect(false);
		}
	}
	registerEditorTypes(types) {
		if (this.#editorTypes) return;
		this.#editorTypes = types;
		for (const editorType of this.#editorTypes) this.#dispatchUpdateUI(editorType.defaultPropertiesToUpdate);
	}
	getId() {
		return this.#idManager.id;
	}
	get currentLayer() {
		return this.#allLayers.get(this.#currentPageIndex);
	}
	getLayer(pageIndex) {
		return this.#allLayers.get(pageIndex);
	}
	get currentPageIndex() {
		return this.#currentPageIndex;
	}
	addLayer(layer) {
		this.#allLayers.set(layer.pageIndex, layer);
		if (this.#isEnabled) layer.enable();
		else layer.disable();
	}
	removeLayer(layer) {
		this.#allLayers.delete(layer.pageIndex);
	}
	async updateMode(mode, editId = null, isFromKeyboard = false) {
		if (this.#mode === mode) return;
		if (this.#updateModeCapability) {
			await this.#updateModeCapability.promise;
			if (!this.#updateModeCapability) return;
		}
		this.#updateModeCapability = Promise.withResolvers();
		this.#mode = mode;
		if (mode === AnnotationEditorType$1.NONE) {
			this.setEditingState(false);
			this.#disableAll();
			this._editorUndoBar?.hide();
			this.#updateModeCapability.resolve();
			return;
		}
		this.setEditingState(true);
		await this.#enableAll();
		this.unselectAll();
		for (const layer of this.#allLayers.values()) layer.updateMode(mode);
		if (!editId) {
			if (isFromKeyboard) this.addNewEditorFromKeyboard();
			this.#updateModeCapability.resolve();
			return;
		}
		for (const editor of this.#allEditors.values()) if (editor.annotationElementId === editId) {
			this.setSelected(editor);
			editor.enterInEditMode();
		} else editor.unselect();
		this.#updateModeCapability.resolve();
	}
	addNewEditorFromKeyboard() {
		if (this.currentLayer.canCreateNewEmptyEditor()) this.currentLayer.addNewEditor();
	}
	updateToolbar(mode) {
		if (mode === this.#mode) return;
		this._eventBus.dispatch("switchannotationeditormode", {
			source: this,
			mode
		});
	}
	updateParams(type, value) {
		if (!this.#editorTypes) return;
		switch (type) {
			case AnnotationEditorParamsType$1.CREATE:
				this.currentLayer.addNewEditor();
				return;
			case AnnotationEditorParamsType$1.HIGHLIGHT_DEFAULT_COLOR:
				this.#mainHighlightColorPicker?.updateColor(value);
				break;
			case AnnotationEditorParamsType$1.HIGHLIGHT_SHOW_ALL:
				this._eventBus.dispatch("reporttelemetry", {
					source: this,
					details: {
						type: "editing",
						data: {
							type: "highlight",
							action: "toggle_visibility"
						}
					}
				});
				(this.#showAllStates ||= /* @__PURE__ */ new Map()).set(type, value);
				this.showAllEditors("highlight", value);
		}
		for (const editor of this.#selectedEditors) editor.updateParams(type, value);
		for (const editorType of this.#editorTypes) editorType.updateDefaultParams(type, value);
	}
	showAllEditors(type, visible, updateButton = false) {
		for (const editor of this.#allEditors.values()) if (editor.editorType === type) editor.show(visible);
		if ((this.#showAllStates?.get(AnnotationEditorParamsType$1.HIGHLIGHT_SHOW_ALL) ?? true) !== visible) this.#dispatchUpdateUI([[AnnotationEditorParamsType$1.HIGHLIGHT_SHOW_ALL, visible]]);
	}
	enableWaiting(mustWait = false) {
		if (this.#isWaiting === mustWait) return;
		this.#isWaiting = mustWait;
		for (const layer of this.#allLayers.values()) {
			if (mustWait) layer.disableClick();
			else layer.enableClick();
			layer.div.classList.toggle("waiting", mustWait);
		}
	}
	async #enableAll() {
		if (!this.#isEnabled) {
			this.#isEnabled = true;
			const promises = [];
			for (const layer of this.#allLayers.values()) promises.push(layer.enable());
			await Promise.all(promises);
			for (const editor of this.#allEditors.values()) editor.enable();
		}
	}
	#disableAll() {
		this.unselectAll();
		if (this.#isEnabled) {
			this.#isEnabled = false;
			for (const layer of this.#allLayers.values()) layer.disable();
			for (const editor of this.#allEditors.values()) editor.disable();
		}
	}
	getEditors(pageIndex) {
		const editors = [];
		for (const editor of this.#allEditors.values()) if (editor.pageIndex === pageIndex) editors.push(editor);
		return editors;
	}
	getEditor(id) {
		return this.#allEditors.get(id);
	}
	addEditor(editor) {
		this.#allEditors.set(editor.id, editor);
	}
	removeEditor(editor) {
		if (editor.div.contains(document.activeElement)) {
			if (this.#focusMainContainerTimeoutId) clearTimeout(this.#focusMainContainerTimeoutId);
			this.#focusMainContainerTimeoutId = setTimeout(() => {
				this.focusMainContainer();
				this.#focusMainContainerTimeoutId = null;
			}, 0);
		}
		this.#allEditors.delete(editor.id);
		this.unselect(editor);
		if (!editor.annotationElementId || !this.#deletedAnnotationsElementIds.has(editor.annotationElementId)) this.#annotationStorage?.remove(editor.id);
	}
	addDeletedAnnotationElement(editor) {
		this.#deletedAnnotationsElementIds.add(editor.annotationElementId);
		this.addChangedExistingAnnotation(editor);
		editor.deleted = true;
	}
	isDeletedAnnotationElement(annotationElementId) {
		return this.#deletedAnnotationsElementIds.has(annotationElementId);
	}
	removeDeletedAnnotationElement(editor) {
		this.#deletedAnnotationsElementIds.delete(editor.annotationElementId);
		this.removeChangedExistingAnnotation(editor);
		editor.deleted = false;
	}
	#addEditorToLayer(editor) {
		const layer = this.#allLayers.get(editor.pageIndex);
		if (layer) layer.addOrRebuild(editor);
		else {
			this.addEditor(editor);
			this.addToAnnotationStorage(editor);
		}
	}
	setActiveEditor(editor) {
		if (this.#activeEditor === editor) return;
		this.#activeEditor = editor;
		if (editor) this.#dispatchUpdateUI(editor.propertiesToUpdate);
	}
	get #lastSelectedEditor() {
		let ed = null;
		for (ed of this.#selectedEditors);
		return ed;
	}
	updateUI(editor) {
		if (this.#lastSelectedEditor === editor) this.#dispatchUpdateUI(editor.propertiesToUpdate);
	}
	updateUIForDefaultProperties(editorType) {
		this.#dispatchUpdateUI(editorType.defaultPropertiesToUpdate);
	}
	toggleSelected(editor) {
		if (this.#selectedEditors.has(editor)) {
			this.#selectedEditors.delete(editor);
			editor.unselect();
			this.#dispatchUpdateStates({ hasSelectedEditor: this.hasSelection });
			return;
		}
		this.#selectedEditors.add(editor);
		editor.select();
		this.#dispatchUpdateUI(editor.propertiesToUpdate);
		this.#dispatchUpdateStates({ hasSelectedEditor: true });
	}
	setSelected(editor) {
		this.#currentDrawingSession?.commitOrRemove();
		for (const ed of this.#selectedEditors) if (ed !== editor) ed.unselect();
		this.#selectedEditors.clear();
		this.#selectedEditors.add(editor);
		editor.select();
		this.#dispatchUpdateUI(editor.propertiesToUpdate);
		this.#dispatchUpdateStates({ hasSelectedEditor: true });
	}
	isSelected(editor) {
		return this.#selectedEditors.has(editor);
	}
	get firstSelectedEditor() {
		return this.#selectedEditors.values().next().value;
	}
	unselect(editor) {
		editor.unselect();
		this.#selectedEditors.delete(editor);
		this.#dispatchUpdateStates({ hasSelectedEditor: this.hasSelection });
	}
	get hasSelection() {
		return this.#selectedEditors.size !== 0;
	}
	get isEnterHandled() {
		return this.#selectedEditors.size === 1 && this.firstSelectedEditor.isEnterHandled;
	}
	undo() {
		this.#commandManager.undo();
		this.#dispatchUpdateStates({
			hasSomethingToUndo: this.#commandManager.hasSomethingToUndo(),
			hasSomethingToRedo: true,
			isEmpty: this.#isEmpty()
		});
		this._editorUndoBar?.hide();
	}
	redo() {
		this.#commandManager.redo();
		this.#dispatchUpdateStates({
			hasSomethingToUndo: true,
			hasSomethingToRedo: this.#commandManager.hasSomethingToRedo(),
			isEmpty: this.#isEmpty()
		});
	}
	addCommands(params) {
		this.#commandManager.add(params);
		this.#dispatchUpdateStates({
			hasSomethingToUndo: true,
			hasSomethingToRedo: false,
			isEmpty: this.#isEmpty()
		});
	}
	cleanUndoStack(type) {
		this.#commandManager.cleanType(type);
	}
	#isEmpty() {
		if (this.#allEditors.size === 0) return true;
		if (this.#allEditors.size === 1) for (const editor of this.#allEditors.values()) return editor.isEmpty();
		return false;
	}
	delete() {
		this.commitOrRemove();
		const drawingEditor = this.currentLayer?.endDrawingSession(true);
		if (!this.hasSelection && !drawingEditor) return;
		const editors = drawingEditor ? [drawingEditor] : [...this.#selectedEditors];
		const cmd = () => {
			this._editorUndoBar?.show(undo, editors.length === 1 ? editors[0].editorType : editors.length);
			for (const editor of editors) editor.remove();
		};
		const undo = () => {
			for (const editor of editors) this.#addEditorToLayer(editor);
		};
		this.addCommands({
			cmd,
			undo,
			mustExec: true
		});
	}
	commitOrRemove() {
		this.#activeEditor?.commitOrRemove();
	}
	hasSomethingToControl() {
		return this.#activeEditor || this.hasSelection;
	}
	#selectEditors(editors) {
		for (const editor of this.#selectedEditors) editor.unselect();
		this.#selectedEditors.clear();
		for (const editor of editors) {
			if (editor.isEmpty()) continue;
			this.#selectedEditors.add(editor);
			editor.select();
		}
		this.#dispatchUpdateStates({ hasSelectedEditor: this.hasSelection });
	}
	selectAll() {
		for (const editor of this.#selectedEditors) editor.commit();
		this.#selectEditors(this.#allEditors.values());
	}
	unselectAll() {
		if (this.#activeEditor) {
			this.#activeEditor.commitOrRemove();
			if (this.#mode !== AnnotationEditorType$1.NONE) return;
		}
		if (this.#currentDrawingSession?.commitOrRemove()) return;
		if (!this.hasSelection) return;
		for (const editor of this.#selectedEditors) editor.unselect();
		this.#selectedEditors.clear();
		this.#dispatchUpdateStates({ hasSelectedEditor: false });
	}
	translateSelectedEditors(x, y, noCommit = false) {
		if (!noCommit) this.commitOrRemove();
		if (!this.hasSelection) return;
		this.#translation[0] += x;
		this.#translation[1] += y;
		const [totalX, totalY] = this.#translation;
		const editors = [...this.#selectedEditors];
		const TIME_TO_WAIT = 1e3;
		if (this.#translationTimeoutId) clearTimeout(this.#translationTimeoutId);
		this.#translationTimeoutId = setTimeout(() => {
			this.#translationTimeoutId = null;
			this.#translation[0] = this.#translation[1] = 0;
			this.addCommands({
				cmd: () => {
					for (const editor of editors) if (this.#allEditors.has(editor.id)) editor.translateInPage(totalX, totalY);
				},
				undo: () => {
					for (const editor of editors) if (this.#allEditors.has(editor.id)) editor.translateInPage(-totalX, -totalY);
				},
				mustExec: false
			});
		}, TIME_TO_WAIT);
		for (const editor of editors) editor.translateInPage(x, y);
	}
	setUpDragSession() {
		if (!this.hasSelection) return;
		this.disableUserSelect(true);
		this.#draggingEditors = /* @__PURE__ */ new Map();
		for (const editor of this.#selectedEditors) this.#draggingEditors.set(editor, {
			savedX: editor.x,
			savedY: editor.y,
			savedPageIndex: editor.pageIndex,
			newX: 0,
			newY: 0,
			newPageIndex: -1
		});
	}
	endDragSession() {
		if (!this.#draggingEditors) return false;
		this.disableUserSelect(false);
		const map = this.#draggingEditors;
		this.#draggingEditors = null;
		let mustBeAddedInUndoStack = false;
		for (const [{ x, y, pageIndex }, value] of map) {
			value.newX = x;
			value.newY = y;
			value.newPageIndex = pageIndex;
			mustBeAddedInUndoStack ||= x !== value.savedX || y !== value.savedY || pageIndex !== value.savedPageIndex;
		}
		if (!mustBeAddedInUndoStack) return false;
		const move = (editor, x, y, pageIndex) => {
			if (this.#allEditors.has(editor.id)) {
				const parent = this.#allLayers.get(pageIndex);
				if (parent) editor._setParentAndPosition(parent, x, y);
				else {
					editor.pageIndex = pageIndex;
					editor.x = x;
					editor.y = y;
				}
			}
		};
		this.addCommands({
			cmd: () => {
				for (const [editor, { newX, newY, newPageIndex }] of map) move(editor, newX, newY, newPageIndex);
			},
			undo: () => {
				for (const [editor, { savedX, savedY, savedPageIndex }] of map) move(editor, savedX, savedY, savedPageIndex);
			},
			mustExec: true
		});
		return true;
	}
	dragSelectedEditors(tx, ty) {
		if (!this.#draggingEditors) return;
		for (const editor of this.#draggingEditors.keys()) editor.drag(tx, ty);
	}
	rebuild(editor) {
		if (editor.parent === null) {
			const parent = this.getLayer(editor.pageIndex);
			if (parent) {
				parent.changeParent(editor);
				parent.addOrRebuild(editor);
			} else {
				this.addEditor(editor);
				this.addToAnnotationStorage(editor);
				editor.rebuild();
			}
		} else editor.parent.addOrRebuild(editor);
	}
	get isEditorHandlingKeyboard() {
		return this.getActive()?.shouldGetKeyboardEvents() || this.#selectedEditors.size === 1 && this.firstSelectedEditor.shouldGetKeyboardEvents();
	}
	isActive(editor) {
		return this.#activeEditor === editor;
	}
	getActive() {
		return this.#activeEditor;
	}
	getMode() {
		return this.#mode;
	}
	get imageManager() {
		return shadow$1(this, "imageManager", new ImageManager());
	}
	getSelectionBoxes(textLayer) {
		if (!textLayer) return null;
		const selection = document.getSelection();
		for (let i = 0, ii = selection.rangeCount; i < ii; i++) if (!textLayer.contains(selection.getRangeAt(i).commonAncestorContainer)) return null;
		const { x: layerX, y: layerY, width: parentWidth, height: parentHeight } = textLayer.getBoundingClientRect();
		let rotator;
		switch (textLayer.getAttribute("data-main-rotation")) {
			case "90":
				rotator = (x, y, w, h) => ({
					x: (y - layerY) / parentHeight,
					y: 1 - (x + w - layerX) / parentWidth,
					width: h / parentHeight,
					height: w / parentWidth
				});
				break;
			case "180":
				rotator = (x, y, w, h) => ({
					x: 1 - (x + w - layerX) / parentWidth,
					y: 1 - (y + h - layerY) / parentHeight,
					width: w / parentWidth,
					height: h / parentHeight
				});
				break;
			case "270":
				rotator = (x, y, w, h) => ({
					x: 1 - (y + h - layerY) / parentHeight,
					y: (x - layerX) / parentWidth,
					width: h / parentHeight,
					height: w / parentWidth
				});
				break;
			default: rotator = (x, y, w, h) => ({
				x: (x - layerX) / parentWidth,
				y: (y - layerY) / parentHeight,
				width: w / parentWidth,
				height: h / parentHeight
			});
		}
		const boxes = [];
		for (let i = 0, ii = selection.rangeCount; i < ii; i++) {
			const range = selection.getRangeAt(i);
			if (range.collapsed) continue;
			for (const { x, y, width, height } of range.getClientRects()) {
				if (width === 0 || height === 0) continue;
				boxes.push(rotator(x, y, width, height));
			}
		}
		return boxes.length === 0 ? null : boxes;
	}
	addChangedExistingAnnotation({ annotationElementId, id }) {
		(this.#changedExistingAnnotations ||= /* @__PURE__ */ new Map()).set(annotationElementId, id);
	}
	removeChangedExistingAnnotation({ annotationElementId }) {
		this.#changedExistingAnnotations?.delete(annotationElementId);
	}
	renderAnnotationElement(annotation) {
		const editorId = this.#changedExistingAnnotations?.get(annotation.data.id);
		if (!editorId) return;
		const editor = this.#annotationStorage.getRawValue(editorId);
		if (!editor) return;
		if (this.#mode === AnnotationEditorType$1.NONE && !editor.hasBeenModified) return;
		editor.renderAnnotationElement(annotation);
	}
};
var AltText = class AltText {
	#altText = null;
	#altTextDecorative = false;
	#altTextButton = null;
	#altTextButtonLabel = null;
	#altTextTooltip = null;
	#altTextTooltipTimeout = null;
	#altTextWasFromKeyBoard = false;
	#badge = null;
	#editor = null;
	#guessedText = null;
	#textWithDisclaimer = null;
	#useNewAltTextFlow = false;
	static #l10nNewButton = null;
	static _l10n = null;
	constructor(editor) {
		this.#editor = editor;
		this.#useNewAltTextFlow = editor._uiManager.useNewAltTextFlow;
		AltText.#l10nNewButton ||= Object.freeze({
			added: "pdfjs-editor-new-alt-text-added-button",
			"added-label": "pdfjs-editor-new-alt-text-added-button-label",
			missing: "pdfjs-editor-new-alt-text-missing-button",
			"missing-label": "pdfjs-editor-new-alt-text-missing-button-label",
			review: "pdfjs-editor-new-alt-text-to-review-button",
			"review-label": "pdfjs-editor-new-alt-text-to-review-button-label"
		});
	}
	static initialize(l10n) {
		AltText._l10n ??= l10n;
	}
	async render() {
		const altText = this.#altTextButton = document.createElement("button");
		altText.className = "altText";
		altText.tabIndex = "0";
		const label = this.#altTextButtonLabel = document.createElement("span");
		altText.append(label);
		if (this.#useNewAltTextFlow) {
			altText.classList.add("new");
			altText.setAttribute("data-l10n-id", AltText.#l10nNewButton.missing);
			label.setAttribute("data-l10n-id", AltText.#l10nNewButton["missing-label"]);
		} else {
			altText.setAttribute("data-l10n-id", "pdfjs-editor-alt-text-button");
			label.setAttribute("data-l10n-id", "pdfjs-editor-alt-text-button-label");
		}
		const signal = this.#editor._uiManager._signal;
		altText.addEventListener("contextmenu", noContextMenu$1, { signal });
		altText.addEventListener("pointerdown", (event) => event.stopPropagation(), { signal });
		const onClick = (event) => {
			event.preventDefault();
			this.#editor._uiManager.editAltText(this.#editor);
			if (this.#useNewAltTextFlow) this.#editor._reportTelemetry({
				action: "pdfjs.image.alt_text.image_status_label_clicked",
				data: { label: this.#label }
			});
		};
		altText.addEventListener("click", onClick, {
			capture: true,
			signal
		});
		altText.addEventListener("keydown", (event) => {
			if (event.target === altText && event.key === "Enter") {
				this.#altTextWasFromKeyBoard = true;
				onClick(event);
			}
		}, { signal });
		await this.#setState();
		return altText;
	}
	get #label() {
		return this.#altText && "added" || this.#altText === null && this.guessedText && "review" || "missing";
	}
	finish() {
		if (!this.#altTextButton) return;
		this.#altTextButton.focus({ focusVisible: this.#altTextWasFromKeyBoard });
		this.#altTextWasFromKeyBoard = false;
	}
	isEmpty() {
		if (this.#useNewAltTextFlow) return this.#altText === null;
		return !this.#altText && !this.#altTextDecorative;
	}
	hasData() {
		if (this.#useNewAltTextFlow) return this.#altText !== null || !!this.#guessedText;
		return this.isEmpty();
	}
	get guessedText() {
		return this.#guessedText;
	}
	async setGuessedText(guessedText) {
		if (this.#altText !== null) return;
		this.#guessedText = guessedText;
		this.#textWithDisclaimer = await AltText._l10n.get("pdfjs-editor-new-alt-text-generated-alt-text-with-disclaimer", { generatedAltText: guessedText });
		this.#setState();
	}
	toggleAltTextBadge(visibility = false) {
		if (!this.#useNewAltTextFlow || this.#altText) {
			this.#badge?.remove();
			this.#badge = null;
			return;
		}
		if (!this.#badge) {
			const badge = this.#badge = document.createElement("div");
			badge.className = "noAltTextBadge";
			this.#editor.div.append(badge);
		}
		this.#badge.classList.toggle("hidden", !visibility);
	}
	serialize(isForCopying) {
		let altText = this.#altText;
		if (!isForCopying && this.#guessedText === altText) altText = this.#textWithDisclaimer;
		return {
			altText,
			decorative: this.#altTextDecorative,
			guessedText: this.#guessedText,
			textWithDisclaimer: this.#textWithDisclaimer
		};
	}
	get data() {
		return {
			altText: this.#altText,
			decorative: this.#altTextDecorative
		};
	}
	set data({ altText, decorative, guessedText, textWithDisclaimer, cancel = false }) {
		if (guessedText) {
			this.#guessedText = guessedText;
			this.#textWithDisclaimer = textWithDisclaimer;
		}
		if (this.#altText === altText && this.#altTextDecorative === decorative) return;
		if (!cancel) {
			this.#altText = altText;
			this.#altTextDecorative = decorative;
		}
		this.#setState();
	}
	toggle(enabled = false) {
		if (!this.#altTextButton) return;
		if (!enabled && this.#altTextTooltipTimeout) {
			clearTimeout(this.#altTextTooltipTimeout);
			this.#altTextTooltipTimeout = null;
		}
		this.#altTextButton.disabled = !enabled;
	}
	shown() {
		this.#editor._reportTelemetry({
			action: "pdfjs.image.alt_text.image_status_label_displayed",
			data: { label: this.#label }
		});
	}
	destroy() {
		this.#altTextButton?.remove();
		this.#altTextButton = null;
		this.#altTextButtonLabel = null;
		this.#altTextTooltip = null;
		this.#badge?.remove();
		this.#badge = null;
	}
	async #setState() {
		const button = this.#altTextButton;
		if (!button) return;
		if (this.#useNewAltTextFlow) {
			button.classList.toggle("done", !!this.#altText);
			button.setAttribute("data-l10n-id", AltText.#l10nNewButton[this.#label]);
			this.#altTextButtonLabel?.setAttribute("data-l10n-id", AltText.#l10nNewButton[`${this.#label}-label`]);
			if (!this.#altText) {
				this.#altTextTooltip?.remove();
				return;
			}
		} else {
			if (!this.#altText && !this.#altTextDecorative) {
				button.classList.remove("done");
				this.#altTextTooltip?.remove();
				return;
			}
			button.classList.add("done");
			button.setAttribute("data-l10n-id", "pdfjs-editor-alt-text-edit-button");
		}
		let tooltip = this.#altTextTooltip;
		if (!tooltip) {
			this.#altTextTooltip = tooltip = document.createElement("span");
			tooltip.className = "tooltip";
			tooltip.setAttribute("role", "tooltip");
			tooltip.id = `alt-text-tooltip-${this.#editor.id}`;
			const DELAY_TO_SHOW_TOOLTIP = 100;
			const signal = this.#editor._uiManager._signal;
			signal.addEventListener("abort", () => {
				clearTimeout(this.#altTextTooltipTimeout);
				this.#altTextTooltipTimeout = null;
			}, { once: true });
			button.addEventListener("mouseenter", () => {
				this.#altTextTooltipTimeout = setTimeout(() => {
					this.#altTextTooltipTimeout = null;
					this.#altTextTooltip.classList.add("show");
					this.#editor._reportTelemetry({ action: "alt_text_tooltip" });
				}, DELAY_TO_SHOW_TOOLTIP);
			}, { signal });
			button.addEventListener("mouseleave", () => {
				if (this.#altTextTooltipTimeout) {
					clearTimeout(this.#altTextTooltipTimeout);
					this.#altTextTooltipTimeout = null;
				}
				this.#altTextTooltip?.classList.remove("show");
			}, { signal });
		}
		if (this.#altTextDecorative) tooltip.setAttribute("data-l10n-id", "pdfjs-editor-alt-text-decorative-tooltip");
		else {
			tooltip.removeAttribute("data-l10n-id");
			tooltip.textContent = this.#altText;
		}
		if (!tooltip.parentNode) button.append(tooltip);
		this.#editor.getImageForAltText()?.setAttribute("aria-describedby", tooltip.id);
	}
};
var TouchManager$1 = class TouchManager$1 {
	#container;
	#isPinching = false;
	#isPinchingStopped = null;
	#isPinchingDisabled;
	#onPinchStart;
	#onPinching;
	#onPinchEnd;
	#signal;
	#touchInfo = null;
	#touchManagerAC;
	#touchMoveAC = null;
	constructor({ container, isPinchingDisabled = null, isPinchingStopped = null, onPinchStart = null, onPinching = null, onPinchEnd = null, signal }) {
		this.#container = container;
		this.#isPinchingStopped = isPinchingStopped;
		this.#isPinchingDisabled = isPinchingDisabled;
		this.#onPinchStart = onPinchStart;
		this.#onPinching = onPinching;
		this.#onPinchEnd = onPinchEnd;
		this.#touchManagerAC = new AbortController();
		this.#signal = AbortSignal.any([signal, this.#touchManagerAC.signal]);
		container.addEventListener("touchstart", this.#onTouchStart.bind(this), {
			passive: false,
			signal: this.#signal
		});
	}
	get MIN_TOUCH_DISTANCE_TO_PINCH() {
		return shadow$1(this, "MIN_TOUCH_DISTANCE_TO_PINCH", 35 / (window.devicePixelRatio || 1));
	}
	#onTouchStart(evt) {
		if (this.#isPinchingDisabled?.() || evt.touches.length < 2) return;
		if (!this.#touchMoveAC) {
			this.#touchMoveAC = new AbortController();
			const signal = AbortSignal.any([this.#signal, this.#touchMoveAC.signal]);
			const container = this.#container;
			const opt = {
				signal,
				passive: false
			};
			container.addEventListener("touchmove", this.#onTouchMove.bind(this), opt);
			container.addEventListener("touchend", this.#onTouchEnd.bind(this), opt);
			container.addEventListener("touchcancel", this.#onTouchEnd.bind(this), opt);
			this.#onPinchStart?.();
		}
		stopEvent$1(evt);
		if (evt.touches.length !== 2 || this.#isPinchingStopped?.()) {
			this.#touchInfo = null;
			return;
		}
		let [touch0, touch1] = evt.touches;
		if (touch0.identifier > touch1.identifier) [touch0, touch1] = [touch1, touch0];
		this.#touchInfo = {
			touch0X: touch0.screenX,
			touch0Y: touch0.screenY,
			touch1X: touch1.screenX,
			touch1Y: touch1.screenY
		};
	}
	#onTouchMove(evt) {
		if (!this.#touchInfo || evt.touches.length !== 2) return;
		let [touch0, touch1] = evt.touches;
		if (touch0.identifier > touch1.identifier) [touch0, touch1] = [touch1, touch0];
		const { screenX: screen0X, screenY: screen0Y } = touch0;
		const { screenX: screen1X, screenY: screen1Y } = touch1;
		const touchInfo = this.#touchInfo;
		const { touch0X: pTouch0X, touch0Y: pTouch0Y, touch1X: pTouch1X, touch1Y: pTouch1Y } = touchInfo;
		const prevGapX = pTouch1X - pTouch0X;
		const prevGapY = pTouch1Y - pTouch0Y;
		const currGapX = screen1X - screen0X;
		const currGapY = screen1Y - screen0Y;
		const distance = Math.hypot(currGapX, currGapY) || 1;
		const pDistance = Math.hypot(prevGapX, prevGapY) || 1;
		if (!this.#isPinching && Math.abs(pDistance - distance) <= TouchManager$1.MIN_TOUCH_DISTANCE_TO_PINCH) return;
		touchInfo.touch0X = screen0X;
		touchInfo.touch0Y = screen0Y;
		touchInfo.touch1X = screen1X;
		touchInfo.touch1Y = screen1Y;
		evt.preventDefault();
		if (!this.#isPinching) {
			this.#isPinching = true;
			return;
		}
		const origin = [(screen0X + screen1X) / 2, (screen0Y + screen1Y) / 2];
		this.#onPinching?.(origin, pDistance, distance);
	}
	#onTouchEnd(evt) {
		this.#touchMoveAC.abort();
		this.#touchMoveAC = null;
		this.#onPinchEnd?.();
		if (!this.#touchInfo) return;
		evt.preventDefault();
		this.#touchInfo = null;
		this.#isPinching = false;
	}
	destroy() {
		this.#touchManagerAC?.abort();
		this.#touchManagerAC = null;
	}
};
var AnnotationEditor = class AnnotationEditor {
	#accessibilityData = null;
	#allResizerDivs = null;
	#altText = null;
	#disabled = false;
	#dragPointerId = null;
	#dragPointerType = "";
	#keepAspectRatio = false;
	#resizersDiv = null;
	#lastPointerCoords = null;
	#savedDimensions = null;
	#focusAC = null;
	#focusedResizerName = "";
	#hasBeenClicked = false;
	#initialRect = null;
	#isEditing = false;
	#isInEditMode = false;
	#isResizerEnabledForKeyboard = false;
	#moveInDOMTimeout = null;
	#prevDragX = 0;
	#prevDragY = 0;
	#telemetryTimeouts = null;
	#touchManager = null;
	_editToolbar = null;
	_initialOptions = Object.create(null);
	_initialData = null;
	_isVisible = true;
	_uiManager = null;
	_focusEventsAllowed = true;
	static _l10n = null;
	static _l10nResizer = null;
	#isDraggable = false;
	#zIndex = AnnotationEditor._zIndex++;
	static _borderLineWidth = -1;
	static _colorManager = new ColorManager();
	static _zIndex = 1;
	static _telemetryTimeout = 1e3;
	static get _resizerKeyboardManager() {
		const resize = AnnotationEditor.prototype._resizeWithKeyboard;
		const small = AnnotationEditorUIManager$1.TRANSLATE_SMALL;
		const big = AnnotationEditorUIManager$1.TRANSLATE_BIG;
		return shadow$1(this, "_resizerKeyboardManager", new KeyboardManager([
			[
				["ArrowLeft", "mac+ArrowLeft"],
				resize,
				{ args: [-small, 0] }
			],
			[
				["ctrl+ArrowLeft", "mac+shift+ArrowLeft"],
				resize,
				{ args: [-big, 0] }
			],
			[
				["ArrowRight", "mac+ArrowRight"],
				resize,
				{ args: [small, 0] }
			],
			[
				["ctrl+ArrowRight", "mac+shift+ArrowRight"],
				resize,
				{ args: [big, 0] }
			],
			[
				["ArrowUp", "mac+ArrowUp"],
				resize,
				{ args: [0, -small] }
			],
			[
				["ctrl+ArrowUp", "mac+shift+ArrowUp"],
				resize,
				{ args: [0, -big] }
			],
			[
				["ArrowDown", "mac+ArrowDown"],
				resize,
				{ args: [0, small] }
			],
			[
				["ctrl+ArrowDown", "mac+shift+ArrowDown"],
				resize,
				{ args: [0, big] }
			],
			[["Escape", "mac+Escape"], AnnotationEditor.prototype._stopResizingWithKeyboard]
		]));
	}
	constructor(parameters) {
		this.parent = parameters.parent;
		this.id = parameters.id;
		this.width = this.height = null;
		this.pageIndex = parameters.parent.pageIndex;
		this.name = parameters.name;
		this.div = null;
		this._uiManager = parameters.uiManager;
		this.annotationElementId = null;
		this._willKeepAspectRatio = false;
		this._initialOptions.isCentered = parameters.isCentered;
		this._structTreeParentId = null;
		const { rotation, rawDims: { pageWidth, pageHeight, pageX, pageY } } = this.parent.viewport;
		this.rotation = rotation;
		this.pageRotation = (360 + rotation - this._uiManager.viewParameters.rotation) % 360;
		this.pageDimensions = [pageWidth, pageHeight];
		this.pageTranslation = [pageX, pageY];
		const [width, height] = this.parentDimensions;
		this.x = parameters.x / width;
		this.y = parameters.y / height;
		this.isAttachedToDOM = false;
		this.deleted = false;
	}
	get editorType() {
		return Object.getPrototypeOf(this).constructor._type;
	}
	static get isDrawer() {
		return false;
	}
	static get _defaultLineColor() {
		return shadow$1(this, "_defaultLineColor", this._colorManager.getHexCode("CanvasText"));
	}
	static deleteAnnotationElement(editor) {
		const fakeEditor = new FakeEditor({
			id: editor.parent.getNextId(),
			parent: editor.parent,
			uiManager: editor._uiManager
		});
		fakeEditor.annotationElementId = editor.annotationElementId;
		fakeEditor.deleted = true;
		fakeEditor._uiManager.addToAnnotationStorage(fakeEditor);
	}
	static initialize(l10n, _uiManager) {
		AnnotationEditor._l10n ??= l10n;
		AnnotationEditor._l10nResizer ||= Object.freeze({
			topLeft: "pdfjs-editor-resizer-top-left",
			topMiddle: "pdfjs-editor-resizer-top-middle",
			topRight: "pdfjs-editor-resizer-top-right",
			middleRight: "pdfjs-editor-resizer-middle-right",
			bottomRight: "pdfjs-editor-resizer-bottom-right",
			bottomMiddle: "pdfjs-editor-resizer-bottom-middle",
			bottomLeft: "pdfjs-editor-resizer-bottom-left",
			middleLeft: "pdfjs-editor-resizer-middle-left"
		});
		if (AnnotationEditor._borderLineWidth !== -1) return;
		const style = getComputedStyle(document.documentElement);
		AnnotationEditor._borderLineWidth = parseFloat(style.getPropertyValue("--outline-width")) || 0;
	}
	static updateDefaultParams(_type, _value) {}
	static get defaultPropertiesToUpdate() {
		return [];
	}
	static isHandlingMimeForPasting(mime) {
		return false;
	}
	static paste(item, parent) {
		unreachable("Not implemented");
	}
	get propertiesToUpdate() {
		return [];
	}
	get _isDraggable() {
		return this.#isDraggable;
	}
	set _isDraggable(value) {
		this.#isDraggable = value;
		this.div?.classList.toggle("draggable", value);
	}
	get isEnterHandled() {
		return true;
	}
	center() {
		const [pageWidth, pageHeight] = this.pageDimensions;
		switch (this.parentRotation) {
			case 90:
				this.x -= this.height * pageHeight / (pageWidth * 2);
				this.y += this.width * pageWidth / (pageHeight * 2);
				break;
			case 180:
				this.x += this.width / 2;
				this.y += this.height / 2;
				break;
			case 270:
				this.x += this.height * pageHeight / (pageWidth * 2);
				this.y -= this.width * pageWidth / (pageHeight * 2);
				break;
			default:
				this.x -= this.width / 2;
				this.y -= this.height / 2;
		}
		this.fixAndSetPosition();
	}
	addCommands(params) {
		this._uiManager.addCommands(params);
	}
	get currentLayer() {
		return this._uiManager.currentLayer;
	}
	setInBackground() {
		this.div.style.zIndex = 0;
	}
	setInForeground() {
		this.div.style.zIndex = this.#zIndex;
	}
	setParent(parent) {
		if (parent !== null) {
			this.pageIndex = parent.pageIndex;
			this.pageDimensions = parent.pageDimensions;
		} else this.#stopResizing();
		this.parent = parent;
	}
	focusin(event) {
		if (!this._focusEventsAllowed) return;
		if (!this.#hasBeenClicked) this.parent.setSelected(this);
		else this.#hasBeenClicked = false;
	}
	focusout(event) {
		if (!this._focusEventsAllowed) return;
		if (!this.isAttachedToDOM) return;
		if (event.relatedTarget?.closest(`#${this.id}`)) return;
		event.preventDefault();
		if (!this.parent?.isMultipleSelection) this.commitOrRemove();
	}
	commitOrRemove() {
		if (this.isEmpty()) this.remove();
		else this.commit();
	}
	commit() {
		this.addToAnnotationStorage();
	}
	addToAnnotationStorage() {
		this._uiManager.addToAnnotationStorage(this);
	}
	setAt(x, y, tx, ty) {
		const [width, height] = this.parentDimensions;
		[tx, ty] = this.screenToPageTranslation(tx, ty);
		this.x = (x + tx) / width;
		this.y = (y + ty) / height;
		this.fixAndSetPosition();
	}
	#translate([width, height], x, y) {
		[x, y] = this.screenToPageTranslation(x, y);
		this.x += x / width;
		this.y += y / height;
		this._onTranslating(this.x, this.y);
		this.fixAndSetPosition();
	}
	translate(x, y) {
		this.#translate(this.parentDimensions, x, y);
	}
	translateInPage(x, y) {
		this.#initialRect ||= [
			this.x,
			this.y,
			this.width,
			this.height
		];
		this.#translate(this.pageDimensions, x, y);
		this.div.scrollIntoView({ block: "nearest" });
	}
	drag(tx, ty) {
		this.#initialRect ||= [
			this.x,
			this.y,
			this.width,
			this.height
		];
		const { div, parentDimensions: [parentWidth, parentHeight] } = this;
		this.x += tx / parentWidth;
		this.y += ty / parentHeight;
		if (this.parent && (this.x < 0 || this.x > 1 || this.y < 0 || this.y > 1)) {
			const { x, y } = this.div.getBoundingClientRect();
			if (this.parent.findNewParent(this, x, y)) {
				this.x -= Math.floor(this.x);
				this.y -= Math.floor(this.y);
			}
		}
		let { x, y } = this;
		const [bx, by] = this.getBaseTranslation();
		x += bx;
		y += by;
		const { style } = div;
		style.left = `${(100 * x).toFixed(2)}%`;
		style.top = `${(100 * y).toFixed(2)}%`;
		this._onTranslating(x, y);
		div.scrollIntoView({ block: "nearest" });
	}
	_onTranslating(x, y) {}
	_onTranslated(x, y) {}
	get _hasBeenMoved() {
		return !!this.#initialRect && (this.#initialRect[0] !== this.x || this.#initialRect[1] !== this.y);
	}
	get _hasBeenResized() {
		return !!this.#initialRect && (this.#initialRect[2] !== this.width || this.#initialRect[3] !== this.height);
	}
	getBaseTranslation() {
		const [parentWidth, parentHeight] = this.parentDimensions;
		const { _borderLineWidth } = AnnotationEditor;
		const x = _borderLineWidth / parentWidth;
		const y = _borderLineWidth / parentHeight;
		switch (this.rotation) {
			case 90: return [-x, y];
			case 180: return [x, y];
			case 270: return [x, -y];
			default: return [-x, -y];
		}
	}
	get _mustFixPosition() {
		return true;
	}
	fixAndSetPosition(rotation = this.rotation) {
		const { div: { style }, pageDimensions: [pageWidth, pageHeight] } = this;
		let { x, y, width, height } = this;
		width *= pageWidth;
		height *= pageHeight;
		x *= pageWidth;
		y *= pageHeight;
		if (this._mustFixPosition) switch (rotation) {
			case 0:
				x = Math.max(0, Math.min(pageWidth - width, x));
				y = Math.max(0, Math.min(pageHeight - height, y));
				break;
			case 90:
				x = Math.max(0, Math.min(pageWidth - height, x));
				y = Math.min(pageHeight, Math.max(width, y));
				break;
			case 180:
				x = Math.min(pageWidth, Math.max(width, x));
				y = Math.min(pageHeight, Math.max(height, y));
				break;
			case 270:
				x = Math.min(pageWidth, Math.max(height, x));
				y = Math.max(0, Math.min(pageHeight - width, y));
		}
		this.x = x /= pageWidth;
		this.y = y /= pageHeight;
		const [bx, by] = this.getBaseTranslation();
		x += bx;
		y += by;
		style.left = `${(100 * x).toFixed(2)}%`;
		style.top = `${(100 * y).toFixed(2)}%`;
		this.moveInDOM();
	}
	static #rotatePoint(x, y, angle) {
		switch (angle) {
			case 90: return [y, -x];
			case 180: return [-x, -y];
			case 270: return [-y, x];
			default: return [x, y];
		}
	}
	screenToPageTranslation(x, y) {
		return AnnotationEditor.#rotatePoint(x, y, this.parentRotation);
	}
	pageTranslationToScreen(x, y) {
		return AnnotationEditor.#rotatePoint(x, y, 360 - this.parentRotation);
	}
	#getRotationMatrix(rotation) {
		switch (rotation) {
			case 90: {
				const [pageWidth, pageHeight] = this.pageDimensions;
				return [
					0,
					-pageWidth / pageHeight,
					pageHeight / pageWidth,
					0
				];
			}
			case 180: return [
				-1,
				0,
				0,
				-1
			];
			case 270: {
				const [pageWidth, pageHeight] = this.pageDimensions;
				return [
					0,
					pageWidth / pageHeight,
					-pageHeight / pageWidth,
					0
				];
			}
			default: return [
				1,
				0,
				0,
				1
			];
		}
	}
	get parentScale() {
		return this._uiManager.viewParameters.realScale;
	}
	get parentRotation() {
		return (this._uiManager.viewParameters.rotation + this.pageRotation) % 360;
	}
	get parentDimensions() {
		const { parentScale, pageDimensions: [pageWidth, pageHeight] } = this;
		return [pageWidth * parentScale, pageHeight * parentScale];
	}
	setDims(width, height) {
		const [parentWidth, parentHeight] = this.parentDimensions;
		const { style } = this.div;
		style.width = `${(100 * width / parentWidth).toFixed(2)}%`;
		if (!this.#keepAspectRatio) style.height = `${(100 * height / parentHeight).toFixed(2)}%`;
	}
	fixDims() {
		const { style } = this.div;
		const { height, width } = style;
		const widthPercent = width.endsWith("%");
		const heightPercent = !this.#keepAspectRatio && height.endsWith("%");
		if (widthPercent && heightPercent) return;
		const [parentWidth, parentHeight] = this.parentDimensions;
		if (!widthPercent) style.width = `${(100 * parseFloat(width) / parentWidth).toFixed(2)}%`;
		if (!this.#keepAspectRatio && !heightPercent) style.height = `${(100 * parseFloat(height) / parentHeight).toFixed(2)}%`;
	}
	getInitialTranslation() {
		return [0, 0];
	}
	#createResizers() {
		if (this.#resizersDiv) return;
		this.#resizersDiv = document.createElement("div");
		this.#resizersDiv.classList.add("resizers");
		const classes = this._willKeepAspectRatio ? [
			"topLeft",
			"topRight",
			"bottomRight",
			"bottomLeft"
		] : [
			"topLeft",
			"topMiddle",
			"topRight",
			"middleRight",
			"bottomRight",
			"bottomMiddle",
			"bottomLeft",
			"middleLeft"
		];
		const signal = this._uiManager._signal;
		for (const name of classes) {
			const div = document.createElement("div");
			this.#resizersDiv.append(div);
			div.classList.add("resizer", name);
			div.setAttribute("data-resizer-name", name);
			div.addEventListener("pointerdown", this.#resizerPointerdown.bind(this, name), { signal });
			div.addEventListener("contextmenu", noContextMenu$1, { signal });
			div.tabIndex = -1;
		}
		this.div.prepend(this.#resizersDiv);
	}
	#resizerPointerdown(name, event) {
		event.preventDefault();
		const { isMac } = util_FeatureTest.platform;
		if (event.button !== 0 || event.ctrlKey && isMac) return;
		this.#altText?.toggle(false);
		const savedDraggable = this._isDraggable;
		this._isDraggable = false;
		this.#lastPointerCoords = [event.screenX, event.screenY];
		const ac = new AbortController();
		const signal = this._uiManager.combinedSignal(ac);
		this.parent.togglePointerEvents(false);
		window.addEventListener("pointermove", this.#resizerPointermove.bind(this, name), {
			passive: true,
			capture: true,
			signal
		});
		window.addEventListener("touchmove", stopEvent$1, {
			passive: false,
			signal
		});
		window.addEventListener("contextmenu", noContextMenu$1, { signal });
		this.#savedDimensions = {
			savedX: this.x,
			savedY: this.y,
			savedWidth: this.width,
			savedHeight: this.height
		};
		const savedParentCursor = this.parent.div.style.cursor;
		const savedCursor = this.div.style.cursor;
		this.div.style.cursor = this.parent.div.style.cursor = window.getComputedStyle(event.target).cursor;
		const pointerUpCallback = () => {
			ac.abort();
			this.parent.togglePointerEvents(true);
			this.#altText?.toggle(true);
			this._isDraggable = savedDraggable;
			this.parent.div.style.cursor = savedParentCursor;
			this.div.style.cursor = savedCursor;
			this.#addResizeToUndoStack();
		};
		window.addEventListener("pointerup", pointerUpCallback, { signal });
		window.addEventListener("blur", pointerUpCallback, { signal });
	}
	#resize(x, y, width, height) {
		this.width = width;
		this.height = height;
		this.x = x;
		this.y = y;
		const [parentWidth, parentHeight] = this.parentDimensions;
		this.setDims(parentWidth * width, parentHeight * height);
		this.fixAndSetPosition();
		this._onResized();
	}
	_onResized() {}
	#addResizeToUndoStack() {
		if (!this.#savedDimensions) return;
		const { savedX, savedY, savedWidth, savedHeight } = this.#savedDimensions;
		this.#savedDimensions = null;
		const newX = this.x;
		const newY = this.y;
		const newWidth = this.width;
		const newHeight = this.height;
		if (newX === savedX && newY === savedY && newWidth === savedWidth && newHeight === savedHeight) return;
		this.addCommands({
			cmd: this.#resize.bind(this, newX, newY, newWidth, newHeight),
			undo: this.#resize.bind(this, savedX, savedY, savedWidth, savedHeight),
			mustExec: true
		});
	}
	static _round(x) {
		return Math.round(x * 1e4) / 1e4;
	}
	#resizerPointermove(name, event) {
		const [parentWidth, parentHeight] = this.parentDimensions;
		const savedX = this.x;
		const savedY = this.y;
		const savedWidth = this.width;
		const savedHeight = this.height;
		const minWidth = AnnotationEditor.MIN_SIZE / parentWidth;
		const minHeight = AnnotationEditor.MIN_SIZE / parentHeight;
		const rotationMatrix = this.#getRotationMatrix(this.rotation);
		const transf = (x, y) => [rotationMatrix[0] * x + rotationMatrix[2] * y, rotationMatrix[1] * x + rotationMatrix[3] * y];
		const invRotationMatrix = this.#getRotationMatrix(360 - this.rotation);
		const invTransf = (x, y) => [invRotationMatrix[0] * x + invRotationMatrix[2] * y, invRotationMatrix[1] * x + invRotationMatrix[3] * y];
		let getPoint;
		let getOpposite;
		let isDiagonal = false;
		let isHorizontal = false;
		switch (name) {
			case "topLeft":
				isDiagonal = true;
				getPoint = (w, h) => [0, 0];
				getOpposite = (w, h) => [w, h];
				break;
			case "topMiddle":
				getPoint = (w, h) => [w / 2, 0];
				getOpposite = (w, h) => [w / 2, h];
				break;
			case "topRight":
				isDiagonal = true;
				getPoint = (w, h) => [w, 0];
				getOpposite = (w, h) => [0, h];
				break;
			case "middleRight":
				isHorizontal = true;
				getPoint = (w, h) => [w, h / 2];
				getOpposite = (w, h) => [0, h / 2];
				break;
			case "bottomRight":
				isDiagonal = true;
				getPoint = (w, h) => [w, h];
				getOpposite = (w, h) => [0, 0];
				break;
			case "bottomMiddle":
				getPoint = (w, h) => [w / 2, h];
				getOpposite = (w, h) => [w / 2, 0];
				break;
			case "bottomLeft":
				isDiagonal = true;
				getPoint = (w, h) => [0, h];
				getOpposite = (w, h) => [w, 0];
				break;
			case "middleLeft":
				isHorizontal = true;
				getPoint = (w, h) => [0, h / 2];
				getOpposite = (w, h) => [w, h / 2];
		}
		const point = getPoint(savedWidth, savedHeight);
		const oppositePoint = getOpposite(savedWidth, savedHeight);
		let transfOppositePoint = transf(...oppositePoint);
		const oppositeX = AnnotationEditor._round(savedX + transfOppositePoint[0]);
		const oppositeY = AnnotationEditor._round(savedY + transfOppositePoint[1]);
		let ratioX = 1;
		let ratioY = 1;
		let deltaX, deltaY;
		if (!event.fromKeyboard) {
			const { screenX, screenY } = event;
			const [lastScreenX, lastScreenY] = this.#lastPointerCoords;
			[deltaX, deltaY] = this.screenToPageTranslation(screenX - lastScreenX, screenY - lastScreenY);
			this.#lastPointerCoords[0] = screenX;
			this.#lastPointerCoords[1] = screenY;
		} else ({deltaX, deltaY} = event);
		[deltaX, deltaY] = invTransf(deltaX / parentWidth, deltaY / parentHeight);
		if (isDiagonal) {
			const oldDiag = Math.hypot(savedWidth, savedHeight);
			ratioX = ratioY = Math.max(Math.min(Math.hypot(oppositePoint[0] - point[0] - deltaX, oppositePoint[1] - point[1] - deltaY) / oldDiag, 1 / savedWidth, 1 / savedHeight), minWidth / savedWidth, minHeight / savedHeight);
		} else if (isHorizontal) ratioX = Math.max(minWidth, Math.min(1, Math.abs(oppositePoint[0] - point[0] - deltaX))) / savedWidth;
		else ratioY = Math.max(minHeight, Math.min(1, Math.abs(oppositePoint[1] - point[1] - deltaY))) / savedHeight;
		const newWidth = AnnotationEditor._round(savedWidth * ratioX);
		const newHeight = AnnotationEditor._round(savedHeight * ratioY);
		transfOppositePoint = transf(...getOpposite(newWidth, newHeight));
		const newX = oppositeX - transfOppositePoint[0];
		const newY = oppositeY - transfOppositePoint[1];
		this.#initialRect ||= [
			this.x,
			this.y,
			this.width,
			this.height
		];
		this.width = newWidth;
		this.height = newHeight;
		this.x = newX;
		this.y = newY;
		this.setDims(parentWidth * newWidth, parentHeight * newHeight);
		this.fixAndSetPosition();
		this._onResizing();
	}
	_onResizing() {}
	altTextFinish() {
		this.#altText?.finish();
	}
	async addEditToolbar() {
		if (this._editToolbar || this.#isInEditMode) return this._editToolbar;
		this._editToolbar = new EditorToolbar(this);
		this.div.append(this._editToolbar.render());
		if (this.#altText) await this._editToolbar.addAltText(this.#altText);
		return this._editToolbar;
	}
	removeEditToolbar() {
		if (!this._editToolbar) return;
		this._editToolbar.remove();
		this._editToolbar = null;
		this.#altText?.destroy();
	}
	addContainer(container) {
		const editToolbarDiv = this._editToolbar?.div;
		if (editToolbarDiv) editToolbarDiv.before(container);
		else this.div.append(container);
	}
	getClientDimensions() {
		return this.div.getBoundingClientRect();
	}
	async addAltTextButton() {
		if (this.#altText) return;
		AltText.initialize(AnnotationEditor._l10n);
		this.#altText = new AltText(this);
		if (this.#accessibilityData) {
			this.#altText.data = this.#accessibilityData;
			this.#accessibilityData = null;
		}
		await this.addEditToolbar();
	}
	get altTextData() {
		return this.#altText?.data;
	}
	set altTextData(data) {
		if (!this.#altText) return;
		this.#altText.data = data;
	}
	get guessedAltText() {
		return this.#altText?.guessedText;
	}
	async setGuessedAltText(text) {
		await this.#altText?.setGuessedText(text);
	}
	serializeAltText(isForCopying) {
		return this.#altText?.serialize(isForCopying);
	}
	hasAltText() {
		return !!this.#altText && !this.#altText.isEmpty();
	}
	hasAltTextData() {
		return this.#altText?.hasData() ?? false;
	}
	render() {
		this.div = document.createElement("div");
		this.div.setAttribute("data-editor-rotation", (360 - this.rotation) % 360);
		this.div.className = this.name;
		this.div.setAttribute("id", this.id);
		this.div.tabIndex = this.#disabled ? -1 : 0;
		if (!this._isVisible) this.div.classList.add("hidden");
		this.setInForeground();
		this.#addFocusListeners();
		const [parentWidth, parentHeight] = this.parentDimensions;
		if (this.parentRotation % 180 !== 0) {
			this.div.style.maxWidth = `${(100 * parentHeight / parentWidth).toFixed(2)}%`;
			this.div.style.maxHeight = `${(100 * parentWidth / parentHeight).toFixed(2)}%`;
		}
		const [tx, ty] = this.getInitialTranslation();
		this.translate(tx, ty);
		bindEvents(this, this.div, ["pointerdown"]);
		if (this.isResizable && this._uiManager._supportsPinchToZoom) this.#touchManager ||= new TouchManager$1({
			container: this.div,
			isPinchingDisabled: () => !this.isSelected,
			onPinchStart: this.#touchPinchStartCallback.bind(this),
			onPinching: this.#touchPinchCallback.bind(this),
			onPinchEnd: this.#touchPinchEndCallback.bind(this),
			signal: this._uiManager._signal
		});
		this._uiManager._editorUndoBar?.hide();
		return this.div;
	}
	#touchPinchStartCallback() {
		this.#savedDimensions = {
			savedX: this.x,
			savedY: this.y,
			savedWidth: this.width,
			savedHeight: this.height
		};
		this.#altText?.toggle(false);
		this.parent.togglePointerEvents(false);
	}
	#touchPinchCallback(_origin, prevDistance, distance) {
		const slowDownFactor = .7;
		let factor = slowDownFactor * (distance / prevDistance) + 1 - slowDownFactor;
		if (factor === 1) return;
		const rotationMatrix = this.#getRotationMatrix(this.rotation);
		const transf = (x, y) => [rotationMatrix[0] * x + rotationMatrix[2] * y, rotationMatrix[1] * x + rotationMatrix[3] * y];
		const [parentWidth, parentHeight] = this.parentDimensions;
		const savedX = this.x;
		const savedY = this.y;
		const savedWidth = this.width;
		const savedHeight = this.height;
		const minWidth = AnnotationEditor.MIN_SIZE / parentWidth;
		const minHeight = AnnotationEditor.MIN_SIZE / parentHeight;
		factor = Math.max(Math.min(factor, 1 / savedWidth, 1 / savedHeight), minWidth / savedWidth, minHeight / savedHeight);
		const newWidth = AnnotationEditor._round(savedWidth * factor);
		const newHeight = AnnotationEditor._round(savedHeight * factor);
		if (newWidth === savedWidth && newHeight === savedHeight) return;
		this.#initialRect ||= [
			savedX,
			savedY,
			savedWidth,
			savedHeight
		];
		const transfCenterPoint = transf(savedWidth / 2, savedHeight / 2);
		const centerX = AnnotationEditor._round(savedX + transfCenterPoint[0]);
		const centerY = AnnotationEditor._round(savedY + transfCenterPoint[1]);
		const newTransfCenterPoint = transf(newWidth / 2, newHeight / 2);
		this.x = centerX - newTransfCenterPoint[0];
		this.y = centerY - newTransfCenterPoint[1];
		this.width = newWidth;
		this.height = newHeight;
		this.setDims(parentWidth * newWidth, parentHeight * newHeight);
		this.fixAndSetPosition();
		this._onResizing();
	}
	#touchPinchEndCallback() {
		this.#altText?.toggle(true);
		this.parent.togglePointerEvents(true);
		this.#addResizeToUndoStack();
	}
	pointerdown(event) {
		const { isMac } = util_FeatureTest.platform;
		if (event.button !== 0 || event.ctrlKey && isMac) {
			event.preventDefault();
			return;
		}
		this.#hasBeenClicked = true;
		if (this._isDraggable) {
			this.#setUpDragSession(event);
			return;
		}
		this.#selectOnPointerEvent(event);
	}
	get isSelected() {
		return this._uiManager.isSelected(this);
	}
	#selectOnPointerEvent(event) {
		const { isMac } = util_FeatureTest.platform;
		if (event.ctrlKey && !isMac || event.shiftKey || event.metaKey && isMac) this.parent.toggleSelected(this);
		else this.parent.setSelected(this);
	}
	#setUpDragSession(event) {
		const { isSelected } = this;
		this._uiManager.setUpDragSession();
		let hasDraggingStarted = false;
		const ac = new AbortController();
		const signal = this._uiManager.combinedSignal(ac);
		const opts = {
			capture: true,
			passive: false,
			signal
		};
		const cancelDrag = (e) => {
			ac.abort();
			this.#dragPointerId = null;
			this.#hasBeenClicked = false;
			if (!this._uiManager.endDragSession()) this.#selectOnPointerEvent(e);
			if (hasDraggingStarted) this._onStopDragging();
		};
		if (isSelected) {
			this.#prevDragX = event.clientX;
			this.#prevDragY = event.clientY;
			this.#dragPointerId = event.pointerId;
			this.#dragPointerType = event.pointerType;
			window.addEventListener("pointermove", (e) => {
				if (!hasDraggingStarted) {
					hasDraggingStarted = true;
					this._onStartDragging();
				}
				const { clientX: x, clientY: y, pointerId } = e;
				if (pointerId !== this.#dragPointerId) {
					stopEvent$1(e);
					return;
				}
				const [tx, ty] = this.screenToPageTranslation(x - this.#prevDragX, y - this.#prevDragY);
				this.#prevDragX = x;
				this.#prevDragY = y;
				this._uiManager.dragSelectedEditors(tx, ty);
			}, opts);
			window.addEventListener("touchmove", stopEvent$1, opts);
			window.addEventListener("pointerdown", (e) => {
				if (e.pointerType === this.#dragPointerType) {
					if (this.#touchManager || e.isPrimary) cancelDrag(e);
				}
				stopEvent$1(e);
			}, opts);
		}
		const pointerUpCallback = (e) => {
			if (!this.#dragPointerId || this.#dragPointerId === e.pointerId) {
				cancelDrag(e);
				return;
			}
			stopEvent$1(e);
		};
		window.addEventListener("pointerup", pointerUpCallback, { signal });
		window.addEventListener("blur", pointerUpCallback, { signal });
	}
	_onStartDragging() {}
	_onStopDragging() {}
	moveInDOM() {
		if (this.#moveInDOMTimeout) clearTimeout(this.#moveInDOMTimeout);
		this.#moveInDOMTimeout = setTimeout(() => {
			this.#moveInDOMTimeout = null;
			this.parent?.moveEditorInDOM(this);
		}, 0);
	}
	_setParentAndPosition(parent, x, y) {
		parent.changeParent(this);
		this.x = x;
		this.y = y;
		this.fixAndSetPosition();
		this._onTranslated();
	}
	getRect(tx, ty, rotation = this.rotation) {
		const scale = this.parentScale;
		const [pageWidth, pageHeight] = this.pageDimensions;
		const [pageX, pageY] = this.pageTranslation;
		const shiftX = tx / scale;
		const shiftY = ty / scale;
		const x = this.x * pageWidth;
		const y = this.y * pageHeight;
		const width = this.width * pageWidth;
		const height = this.height * pageHeight;
		switch (rotation) {
			case 0: return [
				x + shiftX + pageX,
				pageHeight - y - shiftY - height + pageY,
				x + shiftX + width + pageX,
				pageHeight - y - shiftY + pageY
			];
			case 90: return [
				x + shiftY + pageX,
				pageHeight - y + shiftX + pageY,
				x + shiftY + height + pageX,
				pageHeight - y + shiftX + width + pageY
			];
			case 180: return [
				x - shiftX - width + pageX,
				pageHeight - y + shiftY + pageY,
				x - shiftX + pageX,
				pageHeight - y + shiftY + height + pageY
			];
			case 270: return [
				x - shiftY - height + pageX,
				pageHeight - y - shiftX - width + pageY,
				x - shiftY + pageX,
				pageHeight - y - shiftX + pageY
			];
			default: throw new Error("Invalid rotation");
		}
	}
	getRectInCurrentCoords(rect, pageHeight) {
		const [x1, y1, x2, y2] = rect;
		const width = x2 - x1;
		const height = y2 - y1;
		switch (this.rotation) {
			case 0: return [
				x1,
				pageHeight - y2,
				width,
				height
			];
			case 90: return [
				x1,
				pageHeight - y1,
				height,
				width
			];
			case 180: return [
				x2,
				pageHeight - y1,
				width,
				height
			];
			case 270: return [
				x2,
				pageHeight - y2,
				height,
				width
			];
			default: throw new Error("Invalid rotation");
		}
	}
	onceAdded(focus) {}
	isEmpty() {
		return false;
	}
	enableEditMode() {
		this.#isInEditMode = true;
	}
	disableEditMode() {
		this.#isInEditMode = false;
	}
	isInEditMode() {
		return this.#isInEditMode;
	}
	shouldGetKeyboardEvents() {
		return this.#isResizerEnabledForKeyboard;
	}
	needsToBeRebuilt() {
		return this.div && !this.isAttachedToDOM;
	}
	get isOnScreen() {
		const { top, left, bottom, right } = this.getClientDimensions();
		const { innerHeight, innerWidth } = window;
		return left < innerWidth && right > 0 && top < innerHeight && bottom > 0;
	}
	#addFocusListeners() {
		if (this.#focusAC || !this.div) return;
		this.#focusAC = new AbortController();
		const signal = this._uiManager.combinedSignal(this.#focusAC);
		this.div.addEventListener("focusin", this.focusin.bind(this), { signal });
		this.div.addEventListener("focusout", this.focusout.bind(this), { signal });
	}
	rebuild() {
		this.#addFocusListeners();
	}
	rotate(_angle) {}
	resize() {}
	serializeDeleted() {
		return {
			id: this.annotationElementId,
			deleted: true,
			pageIndex: this.pageIndex,
			popupRef: this._initialData?.popupRef || ""
		};
	}
	serialize(isForCopying = false, context = null) {
		unreachable("An editor must be serializable");
	}
	static async deserialize(data, parent, uiManager) {
		const editor = new this.prototype.constructor({
			parent,
			id: parent.getNextId(),
			uiManager
		});
		editor.rotation = data.rotation;
		editor.#accessibilityData = data.accessibilityData;
		const [pageWidth, pageHeight] = editor.pageDimensions;
		const [x, y, width, height] = editor.getRectInCurrentCoords(data.rect, pageHeight);
		editor.x = x / pageWidth;
		editor.y = y / pageHeight;
		editor.width = width / pageWidth;
		editor.height = height / pageHeight;
		return editor;
	}
	get hasBeenModified() {
		return !!this.annotationElementId && (this.deleted || this.serialize() !== null);
	}
	remove() {
		this.#focusAC?.abort();
		this.#focusAC = null;
		if (!this.isEmpty()) this.commit();
		if (this.parent) this.parent.remove(this);
		else this._uiManager.removeEditor(this);
		if (this.#moveInDOMTimeout) {
			clearTimeout(this.#moveInDOMTimeout);
			this.#moveInDOMTimeout = null;
		}
		this.#stopResizing();
		this.removeEditToolbar();
		if (this.#telemetryTimeouts) {
			for (const timeout of this.#telemetryTimeouts.values()) clearTimeout(timeout);
			this.#telemetryTimeouts = null;
		}
		this.parent = null;
		this.#touchManager?.destroy();
		this.#touchManager = null;
	}
	get isResizable() {
		return false;
	}
	makeResizable() {
		if (this.isResizable) {
			this.#createResizers();
			this.#resizersDiv.classList.remove("hidden");
			bindEvents(this, this.div, ["keydown"]);
		}
	}
	get toolbarPosition() {
		return null;
	}
	keydown(event) {
		if (!this.isResizable || event.target !== this.div || event.key !== "Enter") return;
		this._uiManager.setSelected(this);
		this.#savedDimensions = {
			savedX: this.x,
			savedY: this.y,
			savedWidth: this.width,
			savedHeight: this.height
		};
		const children = this.#resizersDiv.children;
		if (!this.#allResizerDivs) {
			this.#allResizerDivs = Array.from(children);
			const boundResizerKeydown = this.#resizerKeydown.bind(this);
			const boundResizerBlur = this.#resizerBlur.bind(this);
			const signal = this._uiManager._signal;
			for (const div of this.#allResizerDivs) {
				const name = div.getAttribute("data-resizer-name");
				div.setAttribute("role", "spinbutton");
				div.addEventListener("keydown", boundResizerKeydown, { signal });
				div.addEventListener("blur", boundResizerBlur, { signal });
				div.addEventListener("focus", this.#resizerFocus.bind(this, name), { signal });
				div.setAttribute("data-l10n-id", AnnotationEditor._l10nResizer[name]);
			}
		}
		const first = this.#allResizerDivs[0];
		let firstPosition = 0;
		for (const div of children) {
			if (div === first) break;
			firstPosition++;
		}
		const nextFirstPosition = (360 - this.rotation + this.parentRotation) % 360 / 90 * (this.#allResizerDivs.length / 4);
		if (nextFirstPosition !== firstPosition) {
			if (nextFirstPosition < firstPosition) for (let i = 0; i < firstPosition - nextFirstPosition; i++) this.#resizersDiv.append(this.#resizersDiv.firstChild);
			else if (nextFirstPosition > firstPosition) for (let i = 0; i < nextFirstPosition - firstPosition; i++) this.#resizersDiv.firstChild.before(this.#resizersDiv.lastChild);
			let i = 0;
			for (const child of children) {
				const name = this.#allResizerDivs[i++].getAttribute("data-resizer-name");
				child.setAttribute("data-l10n-id", AnnotationEditor._l10nResizer[name]);
			}
		}
		this.#setResizerTabIndex(0);
		this.#isResizerEnabledForKeyboard = true;
		this.#resizersDiv.firstChild.focus({ focusVisible: true });
		event.preventDefault();
		event.stopImmediatePropagation();
	}
	#resizerKeydown(event) {
		AnnotationEditor._resizerKeyboardManager.exec(this, event);
	}
	#resizerBlur(event) {
		if (this.#isResizerEnabledForKeyboard && event.relatedTarget?.parentNode !== this.#resizersDiv) this.#stopResizing();
	}
	#resizerFocus(name) {
		this.#focusedResizerName = this.#isResizerEnabledForKeyboard ? name : "";
	}
	#setResizerTabIndex(value) {
		if (!this.#allResizerDivs) return;
		for (const div of this.#allResizerDivs) div.tabIndex = value;
	}
	_resizeWithKeyboard(x, y) {
		if (!this.#isResizerEnabledForKeyboard) return;
		this.#resizerPointermove(this.#focusedResizerName, {
			deltaX: x,
			deltaY: y,
			fromKeyboard: true
		});
	}
	#stopResizing() {
		this.#isResizerEnabledForKeyboard = false;
		this.#setResizerTabIndex(-1);
		this.#addResizeToUndoStack();
	}
	_stopResizingWithKeyboard() {
		this.#stopResizing();
		this.div.focus();
	}
	select() {
		this.makeResizable();
		this.div?.classList.add("selectedEditor");
		if (!this._editToolbar) {
			this.addEditToolbar().then(() => {
				if (this.div?.classList.contains("selectedEditor")) this._editToolbar?.show();
			});
			return;
		}
		this._editToolbar?.show();
		this.#altText?.toggleAltTextBadge(false);
	}
	unselect() {
		this.#resizersDiv?.classList.add("hidden");
		this.div?.classList.remove("selectedEditor");
		if (this.div?.contains(document.activeElement)) this._uiManager.currentLayer.div.focus({ preventScroll: true });
		this._editToolbar?.hide();
		this.#altText?.toggleAltTextBadge(true);
	}
	updateParams(type, value) {}
	disableEditing() {}
	enableEditing() {}
	enterInEditMode() {}
	getImageForAltText() {
		return null;
	}
	get contentDiv() {
		return this.div;
	}
	get isEditing() {
		return this.#isEditing;
	}
	set isEditing(value) {
		this.#isEditing = value;
		if (!this.parent) return;
		if (value) {
			this.parent.setSelected(this);
			this.parent.setActiveEditor(this);
		} else this.parent.setActiveEditor(null);
	}
	setAspectRatio(width, height) {
		this.#keepAspectRatio = true;
		const aspectRatio = width / height;
		const { style } = this.div;
		style.aspectRatio = aspectRatio;
		style.height = "auto";
	}
	static get MIN_SIZE() {
		return 16;
	}
	static canCreateNewEmptyEditor() {
		return true;
	}
	get telemetryInitialData() {
		return { action: "added" };
	}
	get telemetryFinalData() {
		return null;
	}
	_reportTelemetry(data, mustWait = false) {
		if (mustWait) {
			this.#telemetryTimeouts ||= /* @__PURE__ */ new Map();
			const { action } = data;
			let timeout = this.#telemetryTimeouts.get(action);
			if (timeout) clearTimeout(timeout);
			timeout = setTimeout(() => {
				this._reportTelemetry(data);
				this.#telemetryTimeouts.delete(action);
				if (this.#telemetryTimeouts.size === 0) this.#telemetryTimeouts = null;
			}, AnnotationEditor._telemetryTimeout);
			this.#telemetryTimeouts.set(action, timeout);
			return;
		}
		data.type ||= this.editorType;
		this._uiManager._eventBus.dispatch("reporttelemetry", {
			source: this,
			details: {
				type: "editing",
				data
			}
		});
	}
	show(visible = this._isVisible) {
		this.div.classList.toggle("hidden", !visible);
		this._isVisible = visible;
	}
	enable() {
		if (this.div) this.div.tabIndex = 0;
		this.#disabled = false;
	}
	disable() {
		if (this.div) this.div.tabIndex = -1;
		this.#disabled = true;
	}
	renderAnnotationElement(annotation) {
		let content = annotation.container.querySelector(".annotationContent");
		if (!content) {
			content = document.createElement("div");
			content.classList.add("annotationContent", this.editorType);
			annotation.container.prepend(content);
		} else if (content.nodeName === "CANVAS") {
			const canvas = content;
			content = document.createElement("div");
			content.classList.add("annotationContent", this.editorType);
			canvas.before(content);
		}
		return content;
	}
	resetAnnotationElement(annotation) {
		const { firstChild } = annotation.container;
		if (firstChild?.nodeName === "DIV" && firstChild.classList.contains("annotationContent")) firstChild.remove();
	}
};
var FakeEditor = class extends AnnotationEditor {
	constructor(params) {
		super(params);
		this.annotationElementId = params.annotationElementId;
		this.deleted = true;
	}
	serialize() {
		return this.serializeDeleted();
	}
};
var SEED = 3285377520;
var MASK_HIGH = 4294901760;
var MASK_LOW = 65535;
var MurmurHash3_64 = class {
	constructor(seed) {
		this.h1 = seed ? seed & 4294967295 : SEED;
		this.h2 = seed ? seed & 4294967295 : SEED;
	}
	update(input) {
		let data, length;
		if (typeof input === "string") {
			data = new Uint8Array(input.length * 2);
			length = 0;
			for (let i = 0, ii = input.length; i < ii; i++) {
				const code = input.charCodeAt(i);
				if (code <= 255) data[length++] = code;
				else {
					data[length++] = code >>> 8;
					data[length++] = code & 255;
				}
			}
		} else if (ArrayBuffer.isView(input)) {
			data = input.slice();
			length = data.byteLength;
		} else throw new Error("Invalid data format, must be a string or TypedArray.");
		const blockCounts = length >> 2;
		const tailLength = length - blockCounts * 4;
		const dataUint32 = new Uint32Array(data.buffer, 0, blockCounts);
		let k1 = 0, k2 = 0;
		let h1 = this.h1, h2 = this.h2;
		const C1 = 3432918353, C2 = 461845907;
		const C1_LOW = 11601, C2_LOW = 13715;
		for (let i = 0; i < blockCounts; i++) if (i & 1) {
			k1 = dataUint32[i];
			k1 = k1 * C1 & MASK_HIGH | k1 * C1_LOW & MASK_LOW;
			k1 = k1 << 15 | k1 >>> 17;
			k1 = k1 * C2 & MASK_HIGH | k1 * C2_LOW & MASK_LOW;
			h1 ^= k1;
			h1 = h1 << 13 | h1 >>> 19;
			h1 = h1 * 5 + 3864292196;
		} else {
			k2 = dataUint32[i];
			k2 = k2 * C1 & MASK_HIGH | k2 * C1_LOW & MASK_LOW;
			k2 = k2 << 15 | k2 >>> 17;
			k2 = k2 * C2 & MASK_HIGH | k2 * C2_LOW & MASK_LOW;
			h2 ^= k2;
			h2 = h2 << 13 | h2 >>> 19;
			h2 = h2 * 5 + 3864292196;
		}
		k1 = 0;
		switch (tailLength) {
			case 3: k1 ^= data[blockCounts * 4 + 2] << 16;
			case 2: k1 ^= data[blockCounts * 4 + 1] << 8;
			case 1:
				k1 ^= data[blockCounts * 4];
				k1 = k1 * C1 & MASK_HIGH | k1 * C1_LOW & MASK_LOW;
				k1 = k1 << 15 | k1 >>> 17;
				k1 = k1 * C2 & MASK_HIGH | k1 * C2_LOW & MASK_LOW;
				if (blockCounts & 1) h1 ^= k1;
				else h2 ^= k1;
		}
		this.h1 = h1;
		this.h2 = h2;
	}
	hexdigest() {
		let h1 = this.h1, h2 = this.h2;
		h1 ^= h2 >>> 1;
		h1 = h1 * 3981806797 & MASK_HIGH | h1 * 36045 & MASK_LOW;
		h2 = h2 * 4283543511 & MASK_HIGH | ((h2 << 16 | h1 >>> 16) * 2950163797 & MASK_HIGH) >>> 16;
		h1 ^= h2 >>> 1;
		h1 = h1 * 444984403 & MASK_HIGH | h1 * 60499 & MASK_LOW;
		h2 = h2 * 3301882366 & MASK_HIGH | ((h2 << 16 | h1 >>> 16) * 3120437893 & MASK_HIGH) >>> 16;
		h1 ^= h2 >>> 1;
		return (h1 >>> 0).toString(16).padStart(8, "0") + (h2 >>> 0).toString(16).padStart(8, "0");
	}
};
var SerializableEmpty = Object.freeze({
	map: null,
	hash: "",
	transfer: void 0
});
var AnnotationStorage = class {
	#modified = false;
	#modifiedIds = null;
	#storage = /* @__PURE__ */ new Map();
	constructor() {
		this.onSetModified = null;
		this.onResetModified = null;
		this.onAnnotationEditor = null;
	}
	getValue(key, defaultValue) {
		const value = this.#storage.get(key);
		if (value === void 0) return defaultValue;
		return Object.assign(defaultValue, value);
	}
	getRawValue(key) {
		return this.#storage.get(key);
	}
	remove(key) {
		this.#storage.delete(key);
		if (this.#storage.size === 0) this.resetModified();
		if (typeof this.onAnnotationEditor === "function") {
			for (const value of this.#storage.values()) if (value instanceof AnnotationEditor) return;
			this.onAnnotationEditor(null);
		}
	}
	setValue(key, value) {
		const obj = this.#storage.get(key);
		let modified = false;
		if (obj !== void 0) {
			for (const [entry, val] of Object.entries(value)) if (obj[entry] !== val) {
				modified = true;
				obj[entry] = val;
			}
		} else {
			modified = true;
			this.#storage.set(key, value);
		}
		if (modified) this.#setModified();
		if (value instanceof AnnotationEditor && typeof this.onAnnotationEditor === "function") this.onAnnotationEditor(value.constructor._type);
	}
	has(key) {
		return this.#storage.has(key);
	}
	getAll() {
		return this.#storage.size > 0 ? objectFromMap(this.#storage) : null;
	}
	setAll(obj) {
		for (const [key, val] of Object.entries(obj)) this.setValue(key, val);
	}
	get size() {
		return this.#storage.size;
	}
	#setModified() {
		if (!this.#modified) {
			this.#modified = true;
			if (typeof this.onSetModified === "function") this.onSetModified();
		}
	}
	resetModified() {
		if (this.#modified) {
			this.#modified = false;
			if (typeof this.onResetModified === "function") this.onResetModified();
		}
	}
	get print() {
		return new PrintAnnotationStorage(this);
	}
	get serializable() {
		if (this.#storage.size === 0) return SerializableEmpty;
		const map = /* @__PURE__ */ new Map(), hash = new MurmurHash3_64(), transfer = [];
		const context = Object.create(null);
		let hasBitmap = false;
		for (const [key, val] of this.#storage) {
			const serialized = val instanceof AnnotationEditor ? val.serialize(false, context) : val;
			if (serialized) {
				map.set(key, serialized);
				hash.update(`${key}:${JSON.stringify(serialized)}`);
				hasBitmap ||= !!serialized.bitmap;
			}
		}
		if (hasBitmap) {
			for (const value of map.values()) if (value.bitmap) transfer.push(value.bitmap);
		}
		return map.size > 0 ? {
			map,
			hash: hash.hexdigest(),
			transfer
		} : SerializableEmpty;
	}
	get editorStats() {
		let stats = null;
		const typeToEditor = /* @__PURE__ */ new Map();
		for (const value of this.#storage.values()) {
			if (!(value instanceof AnnotationEditor)) continue;
			const editorStats = value.telemetryFinalData;
			if (!editorStats) continue;
			const { type } = editorStats;
			if (!typeToEditor.has(type)) typeToEditor.set(type, Object.getPrototypeOf(value).constructor);
			stats ||= Object.create(null);
			const map = stats[type] ||= /* @__PURE__ */ new Map();
			for (const [key, val] of Object.entries(editorStats)) {
				if (key === "type") continue;
				let counters = map.get(key);
				if (!counters) {
					counters = /* @__PURE__ */ new Map();
					map.set(key, counters);
				}
				const count = counters.get(val) ?? 0;
				counters.set(val, count + 1);
			}
		}
		for (const [type, editor] of typeToEditor) stats[type] = editor.computeTelemetryFinalData(stats[type]);
		return stats;
	}
	resetModifiedIds() {
		this.#modifiedIds = null;
	}
	get modifiedIds() {
		if (this.#modifiedIds) return this.#modifiedIds;
		const ids = [];
		for (const value of this.#storage.values()) {
			if (!(value instanceof AnnotationEditor) || !value.annotationElementId || !value.serialize()) continue;
			ids.push(value.annotationElementId);
		}
		return this.#modifiedIds = {
			ids: new Set(ids),
			hash: ids.join(",")
		};
	}
};
var PrintAnnotationStorage = class extends AnnotationStorage {
	#serializable;
	constructor(parent) {
		super();
		const { map, hash, transfer } = parent.serializable;
		const clone = structuredClone(map, transfer ? { transfer } : null);
		this.#serializable = {
			map: clone,
			hash,
			transfer
		};
	}
	get print() {
		unreachable("Should not call PrintAnnotationStorage.print");
	}
	get serializable() {
		return this.#serializable;
	}
	get modifiedIds() {
		return shadow$1(this, "modifiedIds", {
			ids: /* @__PURE__ */ new Set(),
			hash: ""
		});
	}
};
var FontLoader = class {
	#systemFonts = /* @__PURE__ */ new Set();
	constructor({ ownerDocument = globalThis.document, styleElement = null }) {
		this._document = ownerDocument;
		this.nativeFontFaces = /* @__PURE__ */ new Set();
		this.styleElement = null;
		this.loadingRequests = [];
		this.loadTestFontId = 0;
	}
	addNativeFontFace(nativeFontFace) {
		this.nativeFontFaces.add(nativeFontFace);
		this._document.fonts.add(nativeFontFace);
	}
	removeNativeFontFace(nativeFontFace) {
		this.nativeFontFaces.delete(nativeFontFace);
		this._document.fonts.delete(nativeFontFace);
	}
	insertRule(rule) {
		if (!this.styleElement) {
			this.styleElement = this._document.createElement("style");
			this._document.documentElement.getElementsByTagName("head")[0].append(this.styleElement);
		}
		const styleSheet = this.styleElement.sheet;
		styleSheet.insertRule(rule, styleSheet.cssRules.length);
	}
	clear() {
		for (const nativeFontFace of this.nativeFontFaces) this._document.fonts.delete(nativeFontFace);
		this.nativeFontFaces.clear();
		this.#systemFonts.clear();
		if (this.styleElement) {
			this.styleElement.remove();
			this.styleElement = null;
		}
	}
	async loadSystemFont({ systemFontInfo: info, _inspectFont }) {
		if (!info || this.#systemFonts.has(info.loadedName)) return;
		assert(!this.disableFontFace, "loadSystemFont shouldn't be called when `disableFontFace` is set.");
		if (this.isFontLoadingAPISupported) {
			const { loadedName, src, style } = info;
			const fontFace = new FontFace(loadedName, src, style);
			this.addNativeFontFace(fontFace);
			try {
				await fontFace.load();
				this.#systemFonts.add(loadedName);
				_inspectFont?.(info);
			} catch {
				warn(`Cannot load system font: ${info.baseFontName}, installing it could help to improve PDF rendering.`);
				this.removeNativeFontFace(fontFace);
			}
			return;
		}
		unreachable("Not implemented: loadSystemFont without the Font Loading API.");
	}
	async bind(font) {
		if (font.attached || font.missingFile && !font.systemFontInfo) return;
		font.attached = true;
		if (font.systemFontInfo) {
			await this.loadSystemFont(font);
			return;
		}
		if (this.isFontLoadingAPISupported) {
			const nativeFontFace = font.createNativeFontFace();
			if (nativeFontFace) {
				this.addNativeFontFace(nativeFontFace);
				try {
					await nativeFontFace.loaded;
				} catch (ex) {
					warn(`Failed to load font '${nativeFontFace.family}': '${ex}'.`);
					font.disableFontFace = true;
					throw ex;
				}
			}
			return;
		}
		const rule = font.createFontFaceRule();
		if (rule) {
			this.insertRule(rule);
			if (this.isSyncFontLoadingSupported) return;
			await new Promise((resolve) => {
				const request = this._queueLoadingCallback(resolve);
				this._prepareFontLoadEvent(font, request);
			});
		}
	}
	get isFontLoadingAPISupported() {
		const hasFonts = !!this._document?.fonts;
		return shadow$1(this, "isFontLoadingAPISupported", hasFonts);
	}
	get isSyncFontLoadingSupported() {
		let supported = false;
		if (isNodeJS) supported = true;
		else if (typeof navigator !== "undefined" && typeof navigator?.userAgent === "string" && /Mozilla\/5.0.*?rv:\d+.*? Gecko/.test(navigator.userAgent)) supported = true;
		return shadow$1(this, "isSyncFontLoadingSupported", supported);
	}
	_queueLoadingCallback(callback) {
		function completeRequest() {
			assert(!request.done, "completeRequest() cannot be called twice.");
			request.done = true;
			while (loadingRequests.length > 0 && loadingRequests[0].done) {
				const otherRequest = loadingRequests.shift();
				setTimeout(otherRequest.callback, 0);
			}
		}
		const { loadingRequests } = this;
		const request = {
			done: false,
			complete: completeRequest,
			callback
		};
		loadingRequests.push(request);
		return request;
	}
	get _loadTestFont() {
		const testFont = atob("T1RUTwALAIAAAwAwQ0ZGIDHtZg4AAAOYAAAAgUZGVE1lkzZwAAAEHAAAABxHREVGABQAFQAABDgAAAAeT1MvMlYNYwkAAAEgAAAAYGNtYXABDQLUAAACNAAAAUJoZWFk/xVFDQAAALwAAAA2aGhlYQdkA+oAAAD0AAAAJGhtdHgD6AAAAAAEWAAAAAZtYXhwAAJQAAAAARgAAAAGbmFtZVjmdH4AAAGAAAAAsXBvc3T/hgAzAAADeAAAACAAAQAAAAEAALZRFsRfDzz1AAsD6AAAAADOBOTLAAAAAM4KHDwAAAAAA+gDIQAAAAgAAgAAAAAAAAABAAADIQAAAFoD6AAAAAAD6AABAAAAAAAAAAAAAAAAAAAAAQAAUAAAAgAAAAQD6AH0AAUAAAKKArwAAACMAooCvAAAAeAAMQECAAACAAYJAAAAAAAAAAAAAQAAAAAAAAAAAAAAAFBmRWQAwAAuAC4DIP84AFoDIQAAAAAAAQAAAAAAAAAAACAAIAABAAAADgCuAAEAAAAAAAAAAQAAAAEAAAAAAAEAAQAAAAEAAAAAAAIAAQAAAAEAAAAAAAMAAQAAAAEAAAAAAAQAAQAAAAEAAAAAAAUAAQAAAAEAAAAAAAYAAQAAAAMAAQQJAAAAAgABAAMAAQQJAAEAAgABAAMAAQQJAAIAAgABAAMAAQQJAAMAAgABAAMAAQQJAAQAAgABAAMAAQQJAAUAAgABAAMAAQQJAAYAAgABWABYAAAAAAAAAwAAAAMAAAAcAAEAAAAAADwAAwABAAAAHAAEACAAAAAEAAQAAQAAAC7//wAAAC7////TAAEAAAAAAAABBgAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAAAAAAD/gwAyAAAAAQAAAAAAAAAAAAAAAAAAAAABAAQEAAEBAQJYAAEBASH4DwD4GwHEAvgcA/gXBIwMAYuL+nz5tQXkD5j3CBLnEQACAQEBIVhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYAAABAQAADwACAQEEE/t3Dov6fAH6fAT+fPp8+nwHDosMCvm1Cvm1DAz6fBQAAAAAAAABAAAAAMmJbzEAAAAAzgTjFQAAAADOBOQpAAEAAAAAAAAADAAUAAQAAAABAAAAAgABAAAAAAAAAAAD6AAAAAAAAA==");
		return shadow$1(this, "_loadTestFont", testFont);
	}
	_prepareFontLoadEvent(font, request) {
		function int32(data, offset) {
			return data.charCodeAt(offset) << 24 | data.charCodeAt(offset + 1) << 16 | data.charCodeAt(offset + 2) << 8 | data.charCodeAt(offset + 3) & 255;
		}
		function spliceString(s, offset, remove, insert) {
			const chunk1 = s.substring(0, offset);
			const chunk2 = s.substring(offset + remove);
			return chunk1 + insert + chunk2;
		}
		let i, ii;
		const canvas = this._document.createElement("canvas");
		canvas.width = 1;
		canvas.height = 1;
		const ctx = canvas.getContext("2d");
		let called = 0;
		function isFontReady(name, callback) {
			if (++called > 30) {
				warn("Load test font never loaded.");
				callback();
				return;
			}
			ctx.font = "30px " + name;
			ctx.fillText(".", 0, 20);
			if (ctx.getImageData(0, 0, 1, 1).data[3] > 0) {
				callback();
				return;
			}
			setTimeout(isFontReady.bind(null, name, callback));
		}
		const loadTestFontId = `lt${Date.now()}${this.loadTestFontId++}`;
		let data = this._loadTestFont;
		data = spliceString(data, 976, loadTestFontId.length, loadTestFontId);
		const CFF_CHECKSUM_OFFSET = 16;
		const XXXX_VALUE = 1482184792;
		let checksum = int32(data, CFF_CHECKSUM_OFFSET);
		for (i = 0, ii = loadTestFontId.length - 3; i < ii; i += 4) checksum = checksum - XXXX_VALUE + int32(loadTestFontId, i) | 0;
		if (i < loadTestFontId.length) checksum = checksum - XXXX_VALUE + int32(loadTestFontId + "XXX", i) | 0;
		data = spliceString(data, CFF_CHECKSUM_OFFSET, 4, string32(checksum));
		const rule = `@font-face {font-family:"${loadTestFontId}";src:${`url(data:font/opentype;base64,${btoa(data)});`}}`;
		this.insertRule(rule);
		const div = this._document.createElement("div");
		div.style.visibility = "hidden";
		div.style.width = div.style.height = "10px";
		div.style.position = "absolute";
		div.style.top = div.style.left = "0px";
		for (const name of [font.loadedName, loadTestFontId]) {
			const span = this._document.createElement("span");
			span.textContent = "Hi";
			span.style.fontFamily = name;
			div.append(span);
		}
		this._document.body.append(div);
		isFontReady(loadTestFontId, () => {
			div.remove();
			request.complete();
		});
	}
};
var FontFaceObject = class {
	constructor(translatedData, { disableFontFace = false, fontExtraProperties = false, inspectFont = null }) {
		this.compiledGlyphs = Object.create(null);
		for (const i in translatedData) this[i] = translatedData[i];
		this.disableFontFace = disableFontFace === true;
		this.fontExtraProperties = fontExtraProperties === true;
		this._inspectFont = inspectFont;
	}
	createNativeFontFace() {
		if (!this.data || this.disableFontFace) return null;
		let nativeFontFace;
		if (!this.cssFontInfo) nativeFontFace = new FontFace(this.loadedName, this.data, {});
		else {
			const css = { weight: this.cssFontInfo.fontWeight };
			if (this.cssFontInfo.italicAngle) css.style = `oblique ${this.cssFontInfo.italicAngle}deg`;
			nativeFontFace = new FontFace(this.cssFontInfo.fontFamily, this.data, css);
		}
		this._inspectFont?.(this);
		return nativeFontFace;
	}
	createFontFaceRule() {
		if (!this.data || this.disableFontFace) return null;
		const url = `url(data:${this.mimetype};base64,${toBase64Util(this.data)});`;
		let rule;
		if (!this.cssFontInfo) rule = `@font-face {font-family:"${this.loadedName}";src:${url}}`;
		else {
			let css = `font-weight: ${this.cssFontInfo.fontWeight};`;
			if (this.cssFontInfo.italicAngle) css += `font-style: oblique ${this.cssFontInfo.italicAngle}deg;`;
			rule = `@font-face {font-family:"${this.cssFontInfo.fontFamily}";${css}src:${url}}`;
		}
		this._inspectFont?.(this, url);
		return rule;
	}
	getPathGenerator(objs, character) {
		if (this.compiledGlyphs[character] !== void 0) return this.compiledGlyphs[character];
		const objId = this.loadedName + "_path_" + character;
		let cmds;
		try {
			cmds = objs.get(objId);
		} catch (ex) {
			warn(`getPathGenerator - ignoring character: "${ex}".`);
		}
		const path = new Path2D(cmds || "");
		if (!this.fontExtraProperties) objs.delete(objId);
		return this.compiledGlyphs[character] = path;
	}
};
var CallbackKind = {
	DATA: 1,
	ERROR: 2
};
var StreamKind = {
	CANCEL: 1,
	CANCEL_COMPLETE: 2,
	CLOSE: 3,
	ENQUEUE: 4,
	ERROR: 5,
	PULL: 6,
	PULL_COMPLETE: 7,
	START_COMPLETE: 8
};
function onFn() {}
function wrapReason(ex) {
	if (ex instanceof AbortException$1 || ex instanceof InvalidPDFException$1 || ex instanceof MissingPDFException$1 || ex instanceof PasswordException || ex instanceof UnexpectedResponseException$1 || ex instanceof UnknownErrorException) return ex;
	if (!(ex instanceof Error || typeof ex === "object" && ex !== null)) unreachable("wrapReason: Expected \"reason\" to be a (possibly cloned) Error.");
	switch (ex.name) {
		case "AbortException": return new AbortException$1(ex.message);
		case "InvalidPDFException": return new InvalidPDFException$1(ex.message);
		case "MissingPDFException": return new MissingPDFException$1(ex.message);
		case "PasswordException": return new PasswordException(ex.message, ex.code);
		case "UnexpectedResponseException": return new UnexpectedResponseException$1(ex.message, ex.status);
		case "UnknownErrorException": return new UnknownErrorException(ex.message, ex.details);
	}
	return new UnknownErrorException(ex.message, ex.toString());
}
var MessageHandler = class {
	#messageAC = new AbortController();
	constructor(sourceName, targetName, comObj) {
		this.sourceName = sourceName;
		this.targetName = targetName;
		this.comObj = comObj;
		this.callbackId = 1;
		this.streamId = 1;
		this.streamSinks = Object.create(null);
		this.streamControllers = Object.create(null);
		this.callbackCapabilities = Object.create(null);
		this.actionHandler = Object.create(null);
		comObj.addEventListener("message", this.#onMessage.bind(this), { signal: this.#messageAC.signal });
	}
	#onMessage({ data }) {
		if (data.targetName !== this.sourceName) return;
		if (data.stream) {
			this.#processStreamMessage(data);
			return;
		}
		if (data.callback) {
			const callbackId = data.callbackId;
			const capability = this.callbackCapabilities[callbackId];
			if (!capability) throw new Error(`Cannot resolve callback ${callbackId}`);
			delete this.callbackCapabilities[callbackId];
			if (data.callback === CallbackKind.DATA) capability.resolve(data.data);
			else if (data.callback === CallbackKind.ERROR) capability.reject(wrapReason(data.reason));
			else throw new Error("Unexpected callback case");
			return;
		}
		const action = this.actionHandler[data.action];
		if (!action) throw new Error(`Unknown action from worker: ${data.action}`);
		if (data.callbackId) {
			const sourceName = this.sourceName, targetName = data.sourceName, comObj = this.comObj;
			Promise.try(action, data.data).then(function(result) {
				comObj.postMessage({
					sourceName,
					targetName,
					callback: CallbackKind.DATA,
					callbackId: data.callbackId,
					data: result
				});
			}, function(reason) {
				comObj.postMessage({
					sourceName,
					targetName,
					callback: CallbackKind.ERROR,
					callbackId: data.callbackId,
					reason: wrapReason(reason)
				});
			});
			return;
		}
		if (data.streamId) {
			this.#createStreamSink(data);
			return;
		}
		action(data.data);
	}
	on(actionName, handler) {
		const ah = this.actionHandler;
		if (ah[actionName]) throw new Error(`There is already an actionName called "${actionName}"`);
		ah[actionName] = handler;
	}
	send(actionName, data, transfers) {
		this.comObj.postMessage({
			sourceName: this.sourceName,
			targetName: this.targetName,
			action: actionName,
			data
		}, transfers);
	}
	sendWithPromise(actionName, data, transfers) {
		const callbackId = this.callbackId++;
		const capability = Promise.withResolvers();
		this.callbackCapabilities[callbackId] = capability;
		try {
			this.comObj.postMessage({
				sourceName: this.sourceName,
				targetName: this.targetName,
				action: actionName,
				callbackId,
				data
			}, transfers);
		} catch (ex) {
			capability.reject(ex);
		}
		return capability.promise;
	}
	sendWithStream(actionName, data, queueingStrategy, transfers) {
		const streamId = this.streamId++, sourceName = this.sourceName, targetName = this.targetName, comObj = this.comObj;
		return new ReadableStream({
			start: (controller) => {
				const startCapability = Promise.withResolvers();
				this.streamControllers[streamId] = {
					controller,
					startCall: startCapability,
					pullCall: null,
					cancelCall: null,
					isClosed: false
				};
				comObj.postMessage({
					sourceName,
					targetName,
					action: actionName,
					streamId,
					data,
					desiredSize: controller.desiredSize
				}, transfers);
				return startCapability.promise;
			},
			pull: (controller) => {
				const pullCapability = Promise.withResolvers();
				this.streamControllers[streamId].pullCall = pullCapability;
				comObj.postMessage({
					sourceName,
					targetName,
					stream: StreamKind.PULL,
					streamId,
					desiredSize: controller.desiredSize
				});
				return pullCapability.promise;
			},
			cancel: (reason) => {
				assert(reason instanceof Error, "cancel must have a valid reason");
				const cancelCapability = Promise.withResolvers();
				this.streamControllers[streamId].cancelCall = cancelCapability;
				this.streamControllers[streamId].isClosed = true;
				comObj.postMessage({
					sourceName,
					targetName,
					stream: StreamKind.CANCEL,
					streamId,
					reason: wrapReason(reason)
				});
				return cancelCapability.promise;
			}
		}, queueingStrategy);
	}
	#createStreamSink(data) {
		const streamId = data.streamId, sourceName = this.sourceName, targetName = data.sourceName, comObj = this.comObj;
		const self = this, action = this.actionHandler[data.action];
		const streamSink = {
			enqueue(chunk, size = 1, transfers) {
				if (this.isCancelled) return;
				const lastDesiredSize = this.desiredSize;
				this.desiredSize -= size;
				if (lastDesiredSize > 0 && this.desiredSize <= 0) {
					this.sinkCapability = Promise.withResolvers();
					this.ready = this.sinkCapability.promise;
				}
				comObj.postMessage({
					sourceName,
					targetName,
					stream: StreamKind.ENQUEUE,
					streamId,
					chunk
				}, transfers);
			},
			close() {
				if (this.isCancelled) return;
				this.isCancelled = true;
				comObj.postMessage({
					sourceName,
					targetName,
					stream: StreamKind.CLOSE,
					streamId
				});
				delete self.streamSinks[streamId];
			},
			error(reason) {
				assert(reason instanceof Error, "error must have a valid reason");
				if (this.isCancelled) return;
				this.isCancelled = true;
				comObj.postMessage({
					sourceName,
					targetName,
					stream: StreamKind.ERROR,
					streamId,
					reason: wrapReason(reason)
				});
			},
			sinkCapability: Promise.withResolvers(),
			onPull: null,
			onCancel: null,
			isCancelled: false,
			desiredSize: data.desiredSize,
			ready: null
		};
		streamSink.sinkCapability.resolve();
		streamSink.ready = streamSink.sinkCapability.promise;
		this.streamSinks[streamId] = streamSink;
		Promise.try(action, data.data, streamSink).then(function() {
			comObj.postMessage({
				sourceName,
				targetName,
				stream: StreamKind.START_COMPLETE,
				streamId,
				success: true
			});
		}, function(reason) {
			comObj.postMessage({
				sourceName,
				targetName,
				stream: StreamKind.START_COMPLETE,
				streamId,
				reason: wrapReason(reason)
			});
		});
	}
	#processStreamMessage(data) {
		const streamId = data.streamId, sourceName = this.sourceName, targetName = data.sourceName, comObj = this.comObj;
		const streamController = this.streamControllers[streamId], streamSink = this.streamSinks[streamId];
		switch (data.stream) {
			case StreamKind.START_COMPLETE:
				if (data.success) streamController.startCall.resolve();
				else streamController.startCall.reject(wrapReason(data.reason));
				break;
			case StreamKind.PULL_COMPLETE:
				if (data.success) streamController.pullCall.resolve();
				else streamController.pullCall.reject(wrapReason(data.reason));
				break;
			case StreamKind.PULL:
				if (!streamSink) {
					comObj.postMessage({
						sourceName,
						targetName,
						stream: StreamKind.PULL_COMPLETE,
						streamId,
						success: true
					});
					break;
				}
				if (streamSink.desiredSize <= 0 && data.desiredSize > 0) streamSink.sinkCapability.resolve();
				streamSink.desiredSize = data.desiredSize;
				Promise.try(streamSink.onPull || onFn).then(function() {
					comObj.postMessage({
						sourceName,
						targetName,
						stream: StreamKind.PULL_COMPLETE,
						streamId,
						success: true
					});
				}, function(reason) {
					comObj.postMessage({
						sourceName,
						targetName,
						stream: StreamKind.PULL_COMPLETE,
						streamId,
						reason: wrapReason(reason)
					});
				});
				break;
			case StreamKind.ENQUEUE:
				assert(streamController, "enqueue should have stream controller");
				if (streamController.isClosed) break;
				streamController.controller.enqueue(data.chunk);
				break;
			case StreamKind.CLOSE:
				assert(streamController, "close should have stream controller");
				if (streamController.isClosed) break;
				streamController.isClosed = true;
				streamController.controller.close();
				this.#deleteStreamController(streamController, streamId);
				break;
			case StreamKind.ERROR:
				assert(streamController, "error should have stream controller");
				streamController.controller.error(wrapReason(data.reason));
				this.#deleteStreamController(streamController, streamId);
				break;
			case StreamKind.CANCEL_COMPLETE:
				if (data.success) streamController.cancelCall.resolve();
				else streamController.cancelCall.reject(wrapReason(data.reason));
				this.#deleteStreamController(streamController, streamId);
				break;
			case StreamKind.CANCEL:
				if (!streamSink) break;
				const dataReason = wrapReason(data.reason);
				Promise.try(streamSink.onCancel || onFn, dataReason).then(function() {
					comObj.postMessage({
						sourceName,
						targetName,
						stream: StreamKind.CANCEL_COMPLETE,
						streamId,
						success: true
					});
				}, function(reason) {
					comObj.postMessage({
						sourceName,
						targetName,
						stream: StreamKind.CANCEL_COMPLETE,
						streamId,
						reason: wrapReason(reason)
					});
				});
				streamSink.sinkCapability.reject(dataReason);
				streamSink.isCancelled = true;
				delete this.streamSinks[streamId];
				break;
			default: throw new Error("Unexpected stream case");
		}
	}
	async #deleteStreamController(streamController, streamId) {
		await Promise.allSettled([
			streamController.startCall?.promise,
			streamController.pullCall?.promise,
			streamController.cancelCall?.promise
		]);
		delete this.streamControllers[streamId];
	}
	destroy() {
		this.#messageAC?.abort();
		this.#messageAC = null;
	}
};
var BaseCanvasFactory = class {
	#enableHWA = false;
	constructor({ enableHWA = false }) {
		this.#enableHWA = enableHWA;
	}
	create(width, height) {
		if (width <= 0 || height <= 0) throw new Error("Invalid canvas size");
		const canvas = this._createCanvas(width, height);
		return {
			canvas,
			context: canvas.getContext("2d", { willReadFrequently: !this.#enableHWA })
		};
	}
	reset(canvasAndContext, width, height) {
		if (!canvasAndContext.canvas) throw new Error("Canvas is not specified");
		if (width <= 0 || height <= 0) throw new Error("Invalid canvas size");
		canvasAndContext.canvas.width = width;
		canvasAndContext.canvas.height = height;
	}
	destroy(canvasAndContext) {
		if (!canvasAndContext.canvas) throw new Error("Canvas is not specified");
		canvasAndContext.canvas.width = 0;
		canvasAndContext.canvas.height = 0;
		canvasAndContext.canvas = null;
		canvasAndContext.context = null;
	}
	_createCanvas(width, height) {
		unreachable("Abstract method `_createCanvas` called.");
	}
};
var DOMCanvasFactory = class extends BaseCanvasFactory {
	constructor({ ownerDocument = globalThis.document, enableHWA = false }) {
		super({ enableHWA });
		this._document = ownerDocument;
	}
	_createCanvas(width, height) {
		const canvas = this._document.createElement("canvas");
		canvas.width = width;
		canvas.height = height;
		return canvas;
	}
};
var BaseCMapReaderFactory = class {
	constructor({ baseUrl = null, isCompressed = true }) {
		this.baseUrl = baseUrl;
		this.isCompressed = isCompressed;
	}
	async fetch({ name }) {
		if (!this.baseUrl) throw new Error("Ensure that the `cMapUrl` and `cMapPacked` API parameters are provided.");
		if (!name) throw new Error("CMap name must be specified.");
		const url = this.baseUrl + name + (this.isCompressed ? ".bcmap" : "");
		return this._fetch(url).then((cMapData) => ({
			cMapData,
			isCompressed: this.isCompressed
		})).catch((reason) => {
			throw new Error(`Unable to load ${this.isCompressed ? "binary " : ""}CMap at: ${url}`);
		});
	}
	async _fetch(url) {
		unreachable("Abstract method `_fetch` called.");
	}
};
var DOMCMapReaderFactory = class extends BaseCMapReaderFactory {
	async _fetch(url) {
		const data = await fetchData$1(url, this.isCompressed ? "arraybuffer" : "text");
		return data instanceof ArrayBuffer ? new Uint8Array(data) : stringToBytes(data);
	}
};
var BaseFilterFactory = class {
	addFilter(maps) {
		return "none";
	}
	addHCMFilter(fgColor, bgColor) {
		return "none";
	}
	addAlphaFilter(map) {
		return "none";
	}
	addLuminosityFilter(map) {
		return "none";
	}
	addHighlightHCMFilter(filterName, fgColor, bgColor, newFgColor, newBgColor) {
		return "none";
	}
	destroy(keepHCM = false) {}
};
var DOMFilterFactory = class extends BaseFilterFactory {
	#baseUrl;
	#_cache;
	#_defs;
	#docId;
	#document;
	#_hcmCache;
	#id = 0;
	constructor({ docId, ownerDocument = globalThis.document }) {
		super();
		this.#docId = docId;
		this.#document = ownerDocument;
	}
	get #cache() {
		return this.#_cache ||= /* @__PURE__ */ new Map();
	}
	get #hcmCache() {
		return this.#_hcmCache ||= /* @__PURE__ */ new Map();
	}
	get #defs() {
		if (!this.#_defs) {
			const div = this.#document.createElement("div");
			const { style } = div;
			style.visibility = "hidden";
			style.contain = "strict";
			style.width = style.height = 0;
			style.position = "absolute";
			style.top = style.left = 0;
			style.zIndex = -1;
			const svg = this.#document.createElementNS(SVG_NS, "svg");
			svg.setAttribute("width", 0);
			svg.setAttribute("height", 0);
			this.#_defs = this.#document.createElementNS(SVG_NS, "defs");
			div.append(svg);
			svg.append(this.#_defs);
			this.#document.body.append(div);
		}
		return this.#_defs;
	}
	#createTables(maps) {
		if (maps.length === 1) {
			const mapR = maps[0];
			const buffer = new Array(256);
			for (let i = 0; i < 256; i++) buffer[i] = mapR[i] / 255;
			const table = buffer.join(",");
			return [
				table,
				table,
				table
			];
		}
		const [mapR, mapG, mapB] = maps;
		const bufferR = new Array(256);
		const bufferG = new Array(256);
		const bufferB = new Array(256);
		for (let i = 0; i < 256; i++) {
			bufferR[i] = mapR[i] / 255;
			bufferG[i] = mapG[i] / 255;
			bufferB[i] = mapB[i] / 255;
		}
		return [
			bufferR.join(","),
			bufferG.join(","),
			bufferB.join(",")
		];
	}
	#createUrl(id) {
		if (this.#baseUrl === void 0) {
			this.#baseUrl = "";
			const url = this.#document.URL;
			if (url !== this.#document.baseURI) {
				if (isDataScheme$1(url)) warn("#createUrl: ignore \"data:\"-URL for performance reasons.");
				else this.#baseUrl = url.split("#", 1)[0];
			}
		}
		return `url(${this.#baseUrl}#${id})`;
	}
	addFilter(maps) {
		if (!maps) return "none";
		let value = this.#cache.get(maps);
		if (value) return value;
		const [tableR, tableG, tableB] = this.#createTables(maps);
		const key = maps.length === 1 ? tableR : `${tableR}${tableG}${tableB}`;
		value = this.#cache.get(key);
		if (value) {
			this.#cache.set(maps, value);
			return value;
		}
		const id = `g_${this.#docId}_transfer_map_${this.#id++}`;
		const url = this.#createUrl(id);
		this.#cache.set(maps, url);
		this.#cache.set(key, url);
		const filter = this.#createFilter(id);
		this.#addTransferMapConversion(tableR, tableG, tableB, filter);
		return url;
	}
	addHCMFilter(fgColor, bgColor) {
		const key = `${fgColor}-${bgColor}`;
		const filterName = "base";
		let info = this.#hcmCache.get(filterName);
		if (info?.key === key) return info.url;
		if (info) {
			info.filter?.remove();
			info.key = key;
			info.url = "none";
			info.filter = null;
		} else {
			info = {
				key,
				url: "none",
				filter: null
			};
			this.#hcmCache.set(filterName, info);
		}
		if (!fgColor || !bgColor) return info.url;
		const fgRGB = this.#getRGB(fgColor);
		fgColor = Util$1.makeHexColor(...fgRGB);
		const bgRGB = this.#getRGB(bgColor);
		bgColor = Util$1.makeHexColor(...bgRGB);
		this.#defs.style.color = "";
		if (fgColor === "#000000" && bgColor === "#ffffff" || fgColor === bgColor) return info.url;
		const map = new Array(256);
		for (let i = 0; i <= 255; i++) {
			const x = i / 255;
			map[i] = x <= .03928 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4;
		}
		const table = map.join(",");
		const id = `g_${this.#docId}_hcm_filter`;
		const filter = info.filter = this.#createFilter(id);
		this.#addTransferMapConversion(table, table, table, filter);
		this.#addGrayConversion(filter);
		const getSteps = (c, n) => {
			const start = fgRGB[c] / 255;
			const end = bgRGB[c] / 255;
			const arr = new Array(n + 1);
			for (let i = 0; i <= n; i++) arr[i] = start + i / n * (end - start);
			return arr.join(",");
		};
		this.#addTransferMapConversion(getSteps(0, 5), getSteps(1, 5), getSteps(2, 5), filter);
		info.url = this.#createUrl(id);
		return info.url;
	}
	addAlphaFilter(map) {
		let value = this.#cache.get(map);
		if (value) return value;
		const [tableA] = this.#createTables([map]);
		const key = `alpha_${tableA}`;
		value = this.#cache.get(key);
		if (value) {
			this.#cache.set(map, value);
			return value;
		}
		const id = `g_${this.#docId}_alpha_map_${this.#id++}`;
		const url = this.#createUrl(id);
		this.#cache.set(map, url);
		this.#cache.set(key, url);
		const filter = this.#createFilter(id);
		this.#addTransferMapAlphaConversion(tableA, filter);
		return url;
	}
	addLuminosityFilter(map) {
		let value = this.#cache.get(map || "luminosity");
		if (value) return value;
		let tableA, key;
		if (map) {
			[tableA] = this.#createTables([map]);
			key = `luminosity_${tableA}`;
		} else key = "luminosity";
		value = this.#cache.get(key);
		if (value) {
			this.#cache.set(map, value);
			return value;
		}
		const id = `g_${this.#docId}_luminosity_map_${this.#id++}`;
		const url = this.#createUrl(id);
		this.#cache.set(map, url);
		this.#cache.set(key, url);
		const filter = this.#createFilter(id);
		this.#addLuminosityConversion(filter);
		if (map) this.#addTransferMapAlphaConversion(tableA, filter);
		return url;
	}
	addHighlightHCMFilter(filterName, fgColor, bgColor, newFgColor, newBgColor) {
		const key = `${fgColor}-${bgColor}-${newFgColor}-${newBgColor}`;
		let info = this.#hcmCache.get(filterName);
		if (info?.key === key) return info.url;
		if (info) {
			info.filter?.remove();
			info.key = key;
			info.url = "none";
			info.filter = null;
		} else {
			info = {
				key,
				url: "none",
				filter: null
			};
			this.#hcmCache.set(filterName, info);
		}
		if (!fgColor || !bgColor) return info.url;
		const [fgRGB, bgRGB] = [fgColor, bgColor].map(this.#getRGB.bind(this));
		let fgGray = Math.round(.2126 * fgRGB[0] + .7152 * fgRGB[1] + .0722 * fgRGB[2]);
		let bgGray = Math.round(.2126 * bgRGB[0] + .7152 * bgRGB[1] + .0722 * bgRGB[2]);
		let [newFgRGB, newBgRGB] = [newFgColor, newBgColor].map(this.#getRGB.bind(this));
		if (bgGray < fgGray) [fgGray, bgGray, newFgRGB, newBgRGB] = [
			bgGray,
			fgGray,
			newBgRGB,
			newFgRGB
		];
		this.#defs.style.color = "";
		const getSteps = (fg, bg, n) => {
			const arr = new Array(256);
			const step = (bgGray - fgGray) / n;
			const newStart = fg / 255;
			const newStep = (bg - fg) / (255 * n);
			let prev = 0;
			for (let i = 0; i <= n; i++) {
				const k = Math.round(fgGray + i * step);
				const value = newStart + i * newStep;
				for (let j = prev; j <= k; j++) arr[j] = value;
				prev = k + 1;
			}
			for (let i = prev; i < 256; i++) arr[i] = arr[prev - 1];
			return arr.join(",");
		};
		const id = `g_${this.#docId}_hcm_${filterName}_filter`;
		const filter = info.filter = this.#createFilter(id);
		this.#addGrayConversion(filter);
		this.#addTransferMapConversion(getSteps(newFgRGB[0], newBgRGB[0], 5), getSteps(newFgRGB[1], newBgRGB[1], 5), getSteps(newFgRGB[2], newBgRGB[2], 5), filter);
		info.url = this.#createUrl(id);
		return info.url;
	}
	destroy(keepHCM = false) {
		if (keepHCM && this.#_hcmCache?.size) return;
		this.#_defs?.parentNode.parentNode.remove();
		this.#_defs = null;
		this.#_cache?.clear();
		this.#_cache = null;
		this.#_hcmCache?.clear();
		this.#_hcmCache = null;
		this.#id = 0;
	}
	#addLuminosityConversion(filter) {
		const feColorMatrix = this.#document.createElementNS(SVG_NS, "feColorMatrix");
		feColorMatrix.setAttribute("type", "matrix");
		feColorMatrix.setAttribute("values", "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.3 0.59 0.11 0 0");
		filter.append(feColorMatrix);
	}
	#addGrayConversion(filter) {
		const feColorMatrix = this.#document.createElementNS(SVG_NS, "feColorMatrix");
		feColorMatrix.setAttribute("type", "matrix");
		feColorMatrix.setAttribute("values", "0.2126 0.7152 0.0722 0 0 0.2126 0.7152 0.0722 0 0 0.2126 0.7152 0.0722 0 0 0 0 0 1 0");
		filter.append(feColorMatrix);
	}
	#createFilter(id) {
		const filter = this.#document.createElementNS(SVG_NS, "filter");
		filter.setAttribute("color-interpolation-filters", "sRGB");
		filter.setAttribute("id", id);
		this.#defs.append(filter);
		return filter;
	}
	#appendFeFunc(feComponentTransfer, func, table) {
		const feFunc = this.#document.createElementNS(SVG_NS, func);
		feFunc.setAttribute("type", "discrete");
		feFunc.setAttribute("tableValues", table);
		feComponentTransfer.append(feFunc);
	}
	#addTransferMapConversion(rTable, gTable, bTable, filter) {
		const feComponentTransfer = this.#document.createElementNS(SVG_NS, "feComponentTransfer");
		filter.append(feComponentTransfer);
		this.#appendFeFunc(feComponentTransfer, "feFuncR", rTable);
		this.#appendFeFunc(feComponentTransfer, "feFuncG", gTable);
		this.#appendFeFunc(feComponentTransfer, "feFuncB", bTable);
	}
	#addTransferMapAlphaConversion(aTable, filter) {
		const feComponentTransfer = this.#document.createElementNS(SVG_NS, "feComponentTransfer");
		filter.append(feComponentTransfer);
		this.#appendFeFunc(feComponentTransfer, "feFuncA", aTable);
	}
	#getRGB(color) {
		this.#defs.style.color = color;
		return getRGB(getComputedStyle(this.#defs).getPropertyValue("color"));
	}
};
var BaseStandardFontDataFactory = class {
	constructor({ baseUrl = null }) {
		this.baseUrl = baseUrl;
	}
	async fetch({ filename }) {
		if (!this.baseUrl) throw new Error("Ensure that the `standardFontDataUrl` API parameter is provided.");
		if (!filename) throw new Error("Font filename must be specified.");
		const url = `${this.baseUrl}${filename}`;
		return this._fetch(url).catch((reason) => {
			throw new Error(`Unable to load font data at: ${url}`);
		});
	}
	async _fetch(url) {
		unreachable("Abstract method `_fetch` called.");
	}
};
var DOMStandardFontDataFactory = class extends BaseStandardFontDataFactory {
	async _fetch(url) {
		const data = await fetchData$1(url, "arraybuffer");
		return new Uint8Array(data);
	}
};
if (isNodeJS) warn("Please use the `legacy` build in Node.js environments.");
async function node_utils_fetchData(url) {
	const data = await process.getBuiltinModule("fs").promises.readFile(url);
	return new Uint8Array(data);
}
var NodeFilterFactory = class extends BaseFilterFactory {};
var NodeCanvasFactory = class extends BaseCanvasFactory {
	_createCanvas(width, height) {
		return process.getBuiltinModule("module").createRequire(import.meta.url)("@napi-rs/canvas").createCanvas(width, height);
	}
};
var NodeCMapReaderFactory = class extends BaseCMapReaderFactory {
	async _fetch(url) {
		return node_utils_fetchData(url);
	}
};
var NodeStandardFontDataFactory = class extends BaseStandardFontDataFactory {
	async _fetch(url) {
		return node_utils_fetchData(url);
	}
};
var PathType = {
	FILL: "Fill",
	STROKE: "Stroke",
	SHADING: "Shading"
};
function applyBoundingBox(ctx, bbox) {
	if (!bbox) return;
	const width = bbox[2] - bbox[0];
	const height = bbox[3] - bbox[1];
	const region = new Path2D();
	region.rect(bbox[0], bbox[1], width, height);
	ctx.clip(region);
}
var BaseShadingPattern = class {
	getPattern() {
		unreachable("Abstract method `getPattern` called.");
	}
};
var RadialAxialShadingPattern = class extends BaseShadingPattern {
	constructor(IR) {
		super();
		this._type = IR[1];
		this._bbox = IR[2];
		this._colorStops = IR[3];
		this._p0 = IR[4];
		this._p1 = IR[5];
		this._r0 = IR[6];
		this._r1 = IR[7];
		this.matrix = null;
	}
	_createGradient(ctx) {
		let grad;
		if (this._type === "axial") grad = ctx.createLinearGradient(this._p0[0], this._p0[1], this._p1[0], this._p1[1]);
		else if (this._type === "radial") grad = ctx.createRadialGradient(this._p0[0], this._p0[1], this._r0, this._p1[0], this._p1[1], this._r1);
		for (const colorStop of this._colorStops) grad.addColorStop(colorStop[0], colorStop[1]);
		return grad;
	}
	getPattern(ctx, owner, inverse, pathType) {
		let pattern;
		if (pathType === PathType.STROKE || pathType === PathType.FILL) {
			const ownerBBox = owner.current.getClippedPathBoundingBox(pathType, getCurrentTransform(ctx)) || [
				0,
				0,
				0,
				0
			];
			const width = Math.ceil(ownerBBox[2] - ownerBBox[0]) || 1;
			const height = Math.ceil(ownerBBox[3] - ownerBBox[1]) || 1;
			const tmpCanvas = owner.cachedCanvases.getCanvas("pattern", width, height);
			const tmpCtx = tmpCanvas.context;
			tmpCtx.clearRect(0, 0, tmpCtx.canvas.width, tmpCtx.canvas.height);
			tmpCtx.beginPath();
			tmpCtx.rect(0, 0, tmpCtx.canvas.width, tmpCtx.canvas.height);
			tmpCtx.translate(-ownerBBox[0], -ownerBBox[1]);
			inverse = Util$1.transform(inverse, [
				1,
				0,
				0,
				1,
				ownerBBox[0],
				ownerBBox[1]
			]);
			tmpCtx.transform(...owner.baseTransform);
			if (this.matrix) tmpCtx.transform(...this.matrix);
			applyBoundingBox(tmpCtx, this._bbox);
			tmpCtx.fillStyle = this._createGradient(tmpCtx);
			tmpCtx.fill();
			pattern = ctx.createPattern(tmpCanvas.canvas, "no-repeat");
			const domMatrix = new DOMMatrix(inverse);
			pattern.setTransform(domMatrix);
		} else {
			applyBoundingBox(ctx, this._bbox);
			pattern = this._createGradient(ctx);
		}
		return pattern;
	}
};
function drawTriangle(data, context, p1, p2, p3, c1, c2, c3) {
	const coords = context.coords, colors = context.colors;
	const bytes = data.data, rowSize = data.width * 4;
	let tmp;
	if (coords[p1 + 1] > coords[p2 + 1]) {
		tmp = p1;
		p1 = p2;
		p2 = tmp;
		tmp = c1;
		c1 = c2;
		c2 = tmp;
	}
	if (coords[p2 + 1] > coords[p3 + 1]) {
		tmp = p2;
		p2 = p3;
		p3 = tmp;
		tmp = c2;
		c2 = c3;
		c3 = tmp;
	}
	if (coords[p1 + 1] > coords[p2 + 1]) {
		tmp = p1;
		p1 = p2;
		p2 = tmp;
		tmp = c1;
		c1 = c2;
		c2 = tmp;
	}
	const x1 = (coords[p1] + context.offsetX) * context.scaleX;
	const y1 = (coords[p1 + 1] + context.offsetY) * context.scaleY;
	const x2 = (coords[p2] + context.offsetX) * context.scaleX;
	const y2 = (coords[p2 + 1] + context.offsetY) * context.scaleY;
	const x3 = (coords[p3] + context.offsetX) * context.scaleX;
	const y3 = (coords[p3 + 1] + context.offsetY) * context.scaleY;
	if (y1 >= y3) return;
	const c1r = colors[c1], c1g = colors[c1 + 1], c1b = colors[c1 + 2];
	const c2r = colors[c2], c2g = colors[c2 + 1], c2b = colors[c2 + 2];
	const c3r = colors[c3], c3g = colors[c3 + 1], c3b = colors[c3 + 2];
	const minY = Math.round(y1), maxY = Math.round(y3);
	let xa, car, cag, cab;
	let xb, cbr, cbg, cbb;
	for (let y = minY; y <= maxY; y++) {
		if (y < y2) {
			const k = y < y1 ? 0 : (y1 - y) / (y1 - y2);
			xa = x1 - (x1 - x2) * k;
			car = c1r - (c1r - c2r) * k;
			cag = c1g - (c1g - c2g) * k;
			cab = c1b - (c1b - c2b) * k;
		} else {
			let k;
			if (y > y3) k = 1;
			else if (y2 === y3) k = 0;
			else k = (y2 - y) / (y2 - y3);
			xa = x2 - (x2 - x3) * k;
			car = c2r - (c2r - c3r) * k;
			cag = c2g - (c2g - c3g) * k;
			cab = c2b - (c2b - c3b) * k;
		}
		let k;
		if (y < y1) k = 0;
		else if (y > y3) k = 1;
		else k = (y1 - y) / (y1 - y3);
		xb = x1 - (x1 - x3) * k;
		cbr = c1r - (c1r - c3r) * k;
		cbg = c1g - (c1g - c3g) * k;
		cbb = c1b - (c1b - c3b) * k;
		const x1_ = Math.round(Math.min(xa, xb));
		const x2_ = Math.round(Math.max(xa, xb));
		let j = rowSize * y + x1_ * 4;
		for (let x = x1_; x <= x2_; x++) {
			k = (xa - x) / (xa - xb);
			if (k < 0) k = 0;
			else if (k > 1) k = 1;
			bytes[j++] = car - (car - cbr) * k | 0;
			bytes[j++] = cag - (cag - cbg) * k | 0;
			bytes[j++] = cab - (cab - cbb) * k | 0;
			bytes[j++] = 255;
		}
	}
}
function drawFigure(data, figure, context) {
	const ps = figure.coords;
	const cs = figure.colors;
	let i, ii;
	switch (figure.type) {
		case "lattice":
			const verticesPerRow = figure.verticesPerRow;
			const rows = Math.floor(ps.length / verticesPerRow) - 1;
			const cols = verticesPerRow - 1;
			for (i = 0; i < rows; i++) {
				let q = i * verticesPerRow;
				for (let j = 0; j < cols; j++, q++) {
					drawTriangle(data, context, ps[q], ps[q + 1], ps[q + verticesPerRow], cs[q], cs[q + 1], cs[q + verticesPerRow]);
					drawTriangle(data, context, ps[q + verticesPerRow + 1], ps[q + 1], ps[q + verticesPerRow], cs[q + verticesPerRow + 1], cs[q + 1], cs[q + verticesPerRow]);
				}
			}
			break;
		case "triangles":
			for (i = 0, ii = ps.length; i < ii; i += 3) drawTriangle(data, context, ps[i], ps[i + 1], ps[i + 2], cs[i], cs[i + 1], cs[i + 2]);
			break;
		default: throw new Error("illegal figure");
	}
}
var MeshShadingPattern = class extends BaseShadingPattern {
	constructor(IR) {
		super();
		this._coords = IR[2];
		this._colors = IR[3];
		this._figures = IR[4];
		this._bounds = IR[5];
		this._bbox = IR[7];
		this._background = IR[8];
		this.matrix = null;
	}
	_createMeshCanvas(combinedScale, backgroundColor, cachedCanvases) {
		const EXPECTED_SCALE = 1.1;
		const MAX_PATTERN_SIZE = 3e3;
		const BORDER_SIZE = 2;
		const offsetX = Math.floor(this._bounds[0]);
		const offsetY = Math.floor(this._bounds[1]);
		const boundsWidth = Math.ceil(this._bounds[2]) - offsetX;
		const boundsHeight = Math.ceil(this._bounds[3]) - offsetY;
		const width = Math.min(Math.ceil(Math.abs(boundsWidth * combinedScale[0] * EXPECTED_SCALE)), MAX_PATTERN_SIZE);
		const height = Math.min(Math.ceil(Math.abs(boundsHeight * combinedScale[1] * EXPECTED_SCALE)), MAX_PATTERN_SIZE);
		const scaleX = boundsWidth / width;
		const scaleY = boundsHeight / height;
		const context = {
			coords: this._coords,
			colors: this._colors,
			offsetX: -offsetX,
			offsetY: -offsetY,
			scaleX: 1 / scaleX,
			scaleY: 1 / scaleY
		};
		const paddedWidth = width + 4;
		const paddedHeight = height + 4;
		const tmpCanvas = cachedCanvases.getCanvas("mesh", paddedWidth, paddedHeight);
		const tmpCtx = tmpCanvas.context;
		const data = tmpCtx.createImageData(width, height);
		if (backgroundColor) {
			const bytes = data.data;
			for (let i = 0, ii = bytes.length; i < ii; i += 4) {
				bytes[i] = backgroundColor[0];
				bytes[i + 1] = backgroundColor[1];
				bytes[i + 2] = backgroundColor[2];
				bytes[i + 3] = 255;
			}
		}
		for (const figure of this._figures) drawFigure(data, figure, context);
		tmpCtx.putImageData(data, BORDER_SIZE, BORDER_SIZE);
		return {
			canvas: tmpCanvas.canvas,
			offsetX: offsetX - BORDER_SIZE * scaleX,
			offsetY: offsetY - BORDER_SIZE * scaleY,
			scaleX,
			scaleY
		};
	}
	getPattern(ctx, owner, inverse, pathType) {
		applyBoundingBox(ctx, this._bbox);
		let scale;
		if (pathType === PathType.SHADING) scale = Util$1.singularValueDecompose2dScale(getCurrentTransform(ctx));
		else {
			scale = Util$1.singularValueDecompose2dScale(owner.baseTransform);
			if (this.matrix) {
				const matrixScale = Util$1.singularValueDecompose2dScale(this.matrix);
				scale = [scale[0] * matrixScale[0], scale[1] * matrixScale[1]];
			}
		}
		const temporaryPatternCanvas = this._createMeshCanvas(scale, pathType === PathType.SHADING ? null : this._background, owner.cachedCanvases);
		if (pathType !== PathType.SHADING) {
			ctx.setTransform(...owner.baseTransform);
			if (this.matrix) ctx.transform(...this.matrix);
		}
		ctx.translate(temporaryPatternCanvas.offsetX, temporaryPatternCanvas.offsetY);
		ctx.scale(temporaryPatternCanvas.scaleX, temporaryPatternCanvas.scaleY);
		return ctx.createPattern(temporaryPatternCanvas.canvas, "no-repeat");
	}
};
var DummyShadingPattern = class extends BaseShadingPattern {
	getPattern() {
		return "hotpink";
	}
};
function getShadingPattern(IR) {
	switch (IR[0]) {
		case "RadialAxial": return new RadialAxialShadingPattern(IR);
		case "Mesh": return new MeshShadingPattern(IR);
		case "Dummy": return new DummyShadingPattern();
	}
	throw new Error(`Unknown IR type: ${IR[0]}`);
}
var PaintType = {
	COLORED: 1,
	UNCOLORED: 2
};
var TilingPattern = class TilingPattern {
	static MAX_PATTERN_SIZE = 3e3;
	constructor(IR, color, ctx, canvasGraphicsFactory, baseTransform) {
		this.operatorList = IR[2];
		this.matrix = IR[3];
		this.bbox = IR[4];
		this.xstep = IR[5];
		this.ystep = IR[6];
		this.paintType = IR[7];
		this.tilingType = IR[8];
		this.color = color;
		this.ctx = ctx;
		this.canvasGraphicsFactory = canvasGraphicsFactory;
		this.baseTransform = baseTransform;
	}
	createPatternCanvas(owner) {
		const { bbox, operatorList, paintType, tilingType, color, canvasGraphicsFactory } = this;
		let { xstep, ystep } = this;
		xstep = Math.abs(xstep);
		ystep = Math.abs(ystep);
		info("TilingType: " + tilingType);
		const x0 = bbox[0], y0 = bbox[1], x1 = bbox[2], y1 = bbox[3];
		const width = x1 - x0;
		const height = y1 - y0;
		const matrixScale = Util$1.singularValueDecompose2dScale(this.matrix);
		const curMatrixScale = Util$1.singularValueDecompose2dScale(this.baseTransform);
		const combinedScaleX = matrixScale[0] * curMatrixScale[0];
		const combinedScaleY = matrixScale[1] * curMatrixScale[1];
		let canvasWidth = width, canvasHeight = height, redrawHorizontally = false, redrawVertically = false;
		const xScaledStep = Math.ceil(xstep * combinedScaleX);
		const yScaledStep = Math.ceil(ystep * combinedScaleY);
		const xScaledWidth = Math.ceil(width * combinedScaleX);
		const yScaledHeight = Math.ceil(height * combinedScaleY);
		if (xScaledStep >= xScaledWidth) canvasWidth = xstep;
		else redrawHorizontally = true;
		if (yScaledStep >= yScaledHeight) canvasHeight = ystep;
		else redrawVertically = true;
		const dimx = this.getSizeAndScale(canvasWidth, this.ctx.canvas.width, combinedScaleX);
		const dimy = this.getSizeAndScale(canvasHeight, this.ctx.canvas.height, combinedScaleY);
		const tmpCanvas = owner.cachedCanvases.getCanvas("pattern", dimx.size, dimy.size);
		const tmpCtx = tmpCanvas.context;
		const graphics = canvasGraphicsFactory.createCanvasGraphics(tmpCtx);
		graphics.groupLevel = owner.groupLevel;
		this.setFillAndStrokeStyleToContext(graphics, paintType, color);
		tmpCtx.translate(-dimx.scale * x0, -dimy.scale * y0);
		graphics.transform(dimx.scale, 0, 0, dimy.scale, 0, 0);
		tmpCtx.save();
		this.clipBbox(graphics, x0, y0, x1, y1);
		graphics.baseTransform = getCurrentTransform(graphics.ctx);
		graphics.executeOperatorList(operatorList);
		graphics.endDrawing();
		tmpCtx.restore();
		if (redrawHorizontally || redrawVertically) {
			const image = tmpCanvas.canvas;
			if (redrawHorizontally) canvasWidth = xstep;
			if (redrawVertically) canvasHeight = ystep;
			const dimx2 = this.getSizeAndScale(canvasWidth, this.ctx.canvas.width, combinedScaleX);
			const dimy2 = this.getSizeAndScale(canvasHeight, this.ctx.canvas.height, combinedScaleY);
			const xSize = dimx2.size;
			const ySize = dimy2.size;
			const tmpCanvas2 = owner.cachedCanvases.getCanvas("pattern-workaround", xSize, ySize);
			const tmpCtx2 = tmpCanvas2.context;
			const ii = redrawHorizontally ? Math.floor(width / xstep) : 0;
			const jj = redrawVertically ? Math.floor(height / ystep) : 0;
			for (let i = 0; i <= ii; i++) for (let j = 0; j <= jj; j++) tmpCtx2.drawImage(image, xSize * i, ySize * j, xSize, ySize, 0, 0, xSize, ySize);
			return {
				canvas: tmpCanvas2.canvas,
				scaleX: dimx2.scale,
				scaleY: dimy2.scale,
				offsetX: x0,
				offsetY: y0
			};
		}
		return {
			canvas: tmpCanvas.canvas,
			scaleX: dimx.scale,
			scaleY: dimy.scale,
			offsetX: x0,
			offsetY: y0
		};
	}
	getSizeAndScale(step, realOutputSize, scale) {
		const maxSize = Math.max(TilingPattern.MAX_PATTERN_SIZE, realOutputSize);
		let size = Math.ceil(step * scale);
		if (size >= maxSize) size = maxSize;
		else scale = size / step;
		return {
			scale,
			size
		};
	}
	clipBbox(graphics, x0, y0, x1, y1) {
		const bboxWidth = x1 - x0;
		const bboxHeight = y1 - y0;
		graphics.ctx.rect(x0, y0, bboxWidth, bboxHeight);
		graphics.current.updateRectMinMax(getCurrentTransform(graphics.ctx), [
			x0,
			y0,
			x1,
			y1
		]);
		graphics.clip();
		graphics.endPath();
	}
	setFillAndStrokeStyleToContext(graphics, paintType, color) {
		const context = graphics.ctx, current = graphics.current;
		switch (paintType) {
			case PaintType.COLORED:
				const ctx = this.ctx;
				context.fillStyle = ctx.fillStyle;
				context.strokeStyle = ctx.strokeStyle;
				current.fillColor = ctx.fillStyle;
				current.strokeColor = ctx.strokeStyle;
				break;
			case PaintType.UNCOLORED:
				const cssColor = Util$1.makeHexColor(color[0], color[1], color[2]);
				context.fillStyle = cssColor;
				context.strokeStyle = cssColor;
				current.fillColor = cssColor;
				current.strokeColor = cssColor;
				break;
			default: throw new FormatError(`Unsupported paint type: ${paintType}`);
		}
	}
	getPattern(ctx, owner, inverse, pathType) {
		let matrix = inverse;
		if (pathType !== PathType.SHADING) {
			matrix = Util$1.transform(matrix, owner.baseTransform);
			if (this.matrix) matrix = Util$1.transform(matrix, this.matrix);
		}
		const temporaryPatternCanvas = this.createPatternCanvas(owner);
		let domMatrix = new DOMMatrix(matrix);
		domMatrix = domMatrix.translate(temporaryPatternCanvas.offsetX, temporaryPatternCanvas.offsetY);
		domMatrix = domMatrix.scale(1 / temporaryPatternCanvas.scaleX, 1 / temporaryPatternCanvas.scaleY);
		const pattern = ctx.createPattern(temporaryPatternCanvas.canvas, "repeat");
		pattern.setTransform(domMatrix);
		return pattern;
	}
};
function convertBlackAndWhiteToRGBA({ src, srcPos = 0, dest, width, height, nonBlackColor = 4294967295, inverseDecode = false }) {
	const black = util_FeatureTest.isLittleEndian ? 4278190080 : 255;
	const [zeroMapping, oneMapping] = inverseDecode ? [nonBlackColor, black] : [black, nonBlackColor];
	const widthInSource = width >> 3;
	const widthRemainder = width & 7;
	const srcLength = src.length;
	dest = new Uint32Array(dest.buffer);
	let destPos = 0;
	for (let i = 0; i < height; i++) {
		for (const max = srcPos + widthInSource; srcPos < max; srcPos++) {
			const elem = srcPos < srcLength ? src[srcPos] : 255;
			dest[destPos++] = elem & 128 ? oneMapping : zeroMapping;
			dest[destPos++] = elem & 64 ? oneMapping : zeroMapping;
			dest[destPos++] = elem & 32 ? oneMapping : zeroMapping;
			dest[destPos++] = elem & 16 ? oneMapping : zeroMapping;
			dest[destPos++] = elem & 8 ? oneMapping : zeroMapping;
			dest[destPos++] = elem & 4 ? oneMapping : zeroMapping;
			dest[destPos++] = elem & 2 ? oneMapping : zeroMapping;
			dest[destPos++] = elem & 1 ? oneMapping : zeroMapping;
		}
		if (widthRemainder === 0) continue;
		const elem = srcPos < srcLength ? src[srcPos++] : 255;
		for (let j = 0; j < widthRemainder; j++) dest[destPos++] = elem & 1 << 7 - j ? oneMapping : zeroMapping;
	}
	return {
		srcPos,
		destPos
	};
}
var MIN_FONT_SIZE = 16;
var MAX_FONT_SIZE = 100;
var EXECUTION_TIME = 15;
var EXECUTION_STEPS = 10;
var MAX_SIZE_TO_COMPILE = 1e3;
var FULL_CHUNK_HEIGHT = 16;
function mirrorContextOperations(ctx, destCtx) {
	if (ctx._removeMirroring) throw new Error("Context is already forwarding operations.");
	ctx.__originalSave = ctx.save;
	ctx.__originalRestore = ctx.restore;
	ctx.__originalRotate = ctx.rotate;
	ctx.__originalScale = ctx.scale;
	ctx.__originalTranslate = ctx.translate;
	ctx.__originalTransform = ctx.transform;
	ctx.__originalSetTransform = ctx.setTransform;
	ctx.__originalResetTransform = ctx.resetTransform;
	ctx.__originalClip = ctx.clip;
	ctx.__originalMoveTo = ctx.moveTo;
	ctx.__originalLineTo = ctx.lineTo;
	ctx.__originalBezierCurveTo = ctx.bezierCurveTo;
	ctx.__originalRect = ctx.rect;
	ctx.__originalClosePath = ctx.closePath;
	ctx.__originalBeginPath = ctx.beginPath;
	ctx._removeMirroring = () => {
		ctx.save = ctx.__originalSave;
		ctx.restore = ctx.__originalRestore;
		ctx.rotate = ctx.__originalRotate;
		ctx.scale = ctx.__originalScale;
		ctx.translate = ctx.__originalTranslate;
		ctx.transform = ctx.__originalTransform;
		ctx.setTransform = ctx.__originalSetTransform;
		ctx.resetTransform = ctx.__originalResetTransform;
		ctx.clip = ctx.__originalClip;
		ctx.moveTo = ctx.__originalMoveTo;
		ctx.lineTo = ctx.__originalLineTo;
		ctx.bezierCurveTo = ctx.__originalBezierCurveTo;
		ctx.rect = ctx.__originalRect;
		ctx.closePath = ctx.__originalClosePath;
		ctx.beginPath = ctx.__originalBeginPath;
		delete ctx._removeMirroring;
	};
	ctx.save = function ctxSave() {
		destCtx.save();
		this.__originalSave();
	};
	ctx.restore = function ctxRestore() {
		destCtx.restore();
		this.__originalRestore();
	};
	ctx.translate = function ctxTranslate(x, y) {
		destCtx.translate(x, y);
		this.__originalTranslate(x, y);
	};
	ctx.scale = function ctxScale(x, y) {
		destCtx.scale(x, y);
		this.__originalScale(x, y);
	};
	ctx.transform = function ctxTransform(a, b, c, d, e, f) {
		destCtx.transform(a, b, c, d, e, f);
		this.__originalTransform(a, b, c, d, e, f);
	};
	ctx.setTransform = function ctxSetTransform(a, b, c, d, e, f) {
		destCtx.setTransform(a, b, c, d, e, f);
		this.__originalSetTransform(a, b, c, d, e, f);
	};
	ctx.resetTransform = function ctxResetTransform() {
		destCtx.resetTransform();
		this.__originalResetTransform();
	};
	ctx.rotate = function ctxRotate(angle) {
		destCtx.rotate(angle);
		this.__originalRotate(angle);
	};
	ctx.clip = function ctxRotate(rule) {
		destCtx.clip(rule);
		this.__originalClip(rule);
	};
	ctx.moveTo = function(x, y) {
		destCtx.moveTo(x, y);
		this.__originalMoveTo(x, y);
	};
	ctx.lineTo = function(x, y) {
		destCtx.lineTo(x, y);
		this.__originalLineTo(x, y);
	};
	ctx.bezierCurveTo = function(cp1x, cp1y, cp2x, cp2y, x, y) {
		destCtx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, x, y);
		this.__originalBezierCurveTo(cp1x, cp1y, cp2x, cp2y, x, y);
	};
	ctx.rect = function(x, y, width, height) {
		destCtx.rect(x, y, width, height);
		this.__originalRect(x, y, width, height);
	};
	ctx.closePath = function() {
		destCtx.closePath();
		this.__originalClosePath();
	};
	ctx.beginPath = function() {
		destCtx.beginPath();
		this.__originalBeginPath();
	};
}
var CachedCanvases = class {
	constructor(canvasFactory) {
		this.canvasFactory = canvasFactory;
		this.cache = Object.create(null);
	}
	getCanvas(id, width, height) {
		let canvasEntry;
		if (this.cache[id] !== void 0) {
			canvasEntry = this.cache[id];
			this.canvasFactory.reset(canvasEntry, width, height);
		} else {
			canvasEntry = this.canvasFactory.create(width, height);
			this.cache[id] = canvasEntry;
		}
		return canvasEntry;
	}
	delete(id) {
		delete this.cache[id];
	}
	clear() {
		for (const id in this.cache) {
			const canvasEntry = this.cache[id];
			this.canvasFactory.destroy(canvasEntry);
			delete this.cache[id];
		}
	}
};
function drawImageAtIntegerCoords(ctx, srcImg, srcX, srcY, srcW, srcH, destX, destY, destW, destH) {
	const [a, b, c, d, tx, ty] = getCurrentTransform(ctx);
	if (b === 0 && c === 0) {
		const tlX = destX * a + tx;
		const rTlX = Math.round(tlX);
		const tlY = destY * d + ty;
		const rTlY = Math.round(tlY);
		const brX = (destX + destW) * a + tx;
		const rWidth = Math.abs(Math.round(brX) - rTlX) || 1;
		const brY = (destY + destH) * d + ty;
		const rHeight = Math.abs(Math.round(brY) - rTlY) || 1;
		ctx.setTransform(Math.sign(a), 0, 0, Math.sign(d), rTlX, rTlY);
		ctx.drawImage(srcImg, srcX, srcY, srcW, srcH, 0, 0, rWidth, rHeight);
		ctx.setTransform(a, b, c, d, tx, ty);
		return [rWidth, rHeight];
	}
	if (a === 0 && d === 0) {
		const tlX = destY * c + tx;
		const rTlX = Math.round(tlX);
		const tlY = destX * b + ty;
		const rTlY = Math.round(tlY);
		const brX = (destY + destH) * c + tx;
		const rWidth = Math.abs(Math.round(brX) - rTlX) || 1;
		const brY = (destX + destW) * b + ty;
		const rHeight = Math.abs(Math.round(brY) - rTlY) || 1;
		ctx.setTransform(0, Math.sign(b), Math.sign(c), 0, rTlX, rTlY);
		ctx.drawImage(srcImg, srcX, srcY, srcW, srcH, 0, 0, rHeight, rWidth);
		ctx.setTransform(a, b, c, d, tx, ty);
		return [rHeight, rWidth];
	}
	ctx.drawImage(srcImg, srcX, srcY, srcW, srcH, destX, destY, destW, destH);
	const scaleX = Math.hypot(a, b);
	const scaleY = Math.hypot(c, d);
	return [scaleX * destW, scaleY * destH];
}
function compileType3Glyph(imgData) {
	const { width, height } = imgData;
	if (width > MAX_SIZE_TO_COMPILE || height > MAX_SIZE_TO_COMPILE) return null;
	const POINT_TO_PROCESS_LIMIT = 1e3;
	const POINT_TYPES = new Uint8Array([
		0,
		2,
		4,
		0,
		1,
		0,
		5,
		4,
		8,
		10,
		0,
		8,
		0,
		2,
		1,
		0
	]);
	const width1 = width + 1;
	let points = new Uint8Array(width1 * (height + 1));
	let i, j, j0;
	const lineSize = width + 7 & -8;
	let data = new Uint8Array(lineSize * height), pos = 0;
	for (const elem of imgData.data) {
		let mask = 128;
		while (mask > 0) {
			data[pos++] = elem & mask ? 0 : 255;
			mask >>= 1;
		}
	}
	let count = 0;
	pos = 0;
	if (data[pos] !== 0) {
		points[0] = 1;
		++count;
	}
	for (j = 1; j < width; j++) {
		if (data[pos] !== data[pos + 1]) {
			points[j] = data[pos] ? 2 : 1;
			++count;
		}
		pos++;
	}
	if (data[pos] !== 0) {
		points[j] = 2;
		++count;
	}
	for (i = 1; i < height; i++) {
		pos = i * lineSize;
		j0 = i * width1;
		if (data[pos - lineSize] !== data[pos]) {
			points[j0] = data[pos] ? 1 : 8;
			++count;
		}
		let sum = (data[pos] ? 4 : 0) + (data[pos - lineSize] ? 8 : 0);
		for (j = 1; j < width; j++) {
			sum = (sum >> 2) + (data[pos + 1] ? 4 : 0) + (data[pos - lineSize + 1] ? 8 : 0);
			if (POINT_TYPES[sum]) {
				points[j0 + j] = POINT_TYPES[sum];
				++count;
			}
			pos++;
		}
		if (data[pos - lineSize] !== data[pos]) {
			points[j0 + j] = data[pos] ? 2 : 4;
			++count;
		}
		if (count > POINT_TO_PROCESS_LIMIT) return null;
	}
	pos = lineSize * (height - 1);
	j0 = i * width1;
	if (data[pos] !== 0) {
		points[j0] = 8;
		++count;
	}
	for (j = 1; j < width; j++) {
		if (data[pos] !== data[pos + 1]) {
			points[j0 + j] = data[pos] ? 4 : 8;
			++count;
		}
		pos++;
	}
	if (data[pos] !== 0) {
		points[j0 + j] = 4;
		++count;
	}
	if (count > POINT_TO_PROCESS_LIMIT) return null;
	const steps = new Int32Array([
		0,
		width1,
		-1,
		0,
		-width1,
		0,
		0,
		0,
		1
	]);
	const path = new Path2D();
	for (i = 0; count && i <= height; i++) {
		let p = i * width1;
		const end = p + width;
		while (p < end && !points[p]) p++;
		if (p === end) continue;
		path.moveTo(p % width1, i);
		const p0 = p;
		let type = points[p];
		do {
			const step = steps[type];
			do
				p += step;
			while (!points[p]);
			const pp = points[p];
			if (pp !== 5 && pp !== 10) {
				type = pp;
				points[p] = 0;
			} else {
				type = pp & 51 * type >> 4;
				points[p] &= type >> 2 | type << 2;
			}
			path.lineTo(p % width1, p / width1 | 0);
			if (!points[p]) --count;
		} while (p0 !== p);
		--i;
	}
	data = null;
	points = null;
	const drawOutline = function(c) {
		c.save();
		c.scale(1 / width, -1 / height);
		c.translate(0, -height);
		c.fill(path);
		c.beginPath();
		c.restore();
	};
	return drawOutline;
}
var CanvasExtraState = class {
	constructor(width, height) {
		this.alphaIsShape = false;
		this.fontSize = 0;
		this.fontSizeScale = 1;
		this.textMatrix = IDENTITY_MATRIX;
		this.textMatrixScale = 1;
		this.fontMatrix = FONT_IDENTITY_MATRIX;
		this.leading = 0;
		this.x = 0;
		this.y = 0;
		this.lineX = 0;
		this.lineY = 0;
		this.charSpacing = 0;
		this.wordSpacing = 0;
		this.textHScale = 1;
		this.textRenderingMode = TextRenderingMode.FILL;
		this.textRise = 0;
		this.fillColor = "#000000";
		this.strokeColor = "#000000";
		this.patternFill = false;
		this.patternStroke = false;
		this.fillAlpha = 1;
		this.strokeAlpha = 1;
		this.lineWidth = 1;
		this.activeSMask = null;
		this.transferMaps = "none";
		this.startNewPathAndClipBox([
			0,
			0,
			width,
			height
		]);
	}
	clone() {
		const clone = Object.create(this);
		clone.clipBox = this.clipBox.slice();
		return clone;
	}
	setCurrentPoint(x, y) {
		this.x = x;
		this.y = y;
	}
	updatePathMinMax(transform, x, y) {
		[x, y] = Util$1.applyTransform([x, y], transform);
		this.minX = Math.min(this.minX, x);
		this.minY = Math.min(this.minY, y);
		this.maxX = Math.max(this.maxX, x);
		this.maxY = Math.max(this.maxY, y);
	}
	updateRectMinMax(transform, rect) {
		const p1 = Util$1.applyTransform(rect, transform);
		const p2 = Util$1.applyTransform(rect.slice(2), transform);
		const p3 = Util$1.applyTransform([rect[0], rect[3]], transform);
		const p4 = Util$1.applyTransform([rect[2], rect[1]], transform);
		this.minX = Math.min(this.minX, p1[0], p2[0], p3[0], p4[0]);
		this.minY = Math.min(this.minY, p1[1], p2[1], p3[1], p4[1]);
		this.maxX = Math.max(this.maxX, p1[0], p2[0], p3[0], p4[0]);
		this.maxY = Math.max(this.maxY, p1[1], p2[1], p3[1], p4[1]);
	}
	updateScalingPathMinMax(transform, minMax) {
		Util$1.scaleMinMax(transform, minMax);
		this.minX = Math.min(this.minX, minMax[0]);
		this.minY = Math.min(this.minY, minMax[1]);
		this.maxX = Math.max(this.maxX, minMax[2]);
		this.maxY = Math.max(this.maxY, minMax[3]);
	}
	updateCurvePathMinMax(transform, x0, y0, x1, y1, x2, y2, x3, y3, minMax) {
		const box = Util$1.bezierBoundingBox(x0, y0, x1, y1, x2, y2, x3, y3, minMax);
		if (minMax) return;
		this.updateRectMinMax(transform, box);
	}
	getPathBoundingBox(pathType = PathType.FILL, transform = null) {
		const box = [
			this.minX,
			this.minY,
			this.maxX,
			this.maxY
		];
		if (pathType === PathType.STROKE) {
			if (!transform) unreachable("Stroke bounding box must include transform.");
			const scale = Util$1.singularValueDecompose2dScale(transform);
			const xStrokePad = scale[0] * this.lineWidth / 2;
			const yStrokePad = scale[1] * this.lineWidth / 2;
			box[0] -= xStrokePad;
			box[1] -= yStrokePad;
			box[2] += xStrokePad;
			box[3] += yStrokePad;
		}
		return box;
	}
	updateClipFromPath() {
		const intersect = Util$1.intersect(this.clipBox, this.getPathBoundingBox());
		this.startNewPathAndClipBox(intersect || [
			0,
			0,
			0,
			0
		]);
	}
	isEmptyClip() {
		return this.minX === Infinity;
	}
	startNewPathAndClipBox(box) {
		this.clipBox = box;
		this.minX = Infinity;
		this.minY = Infinity;
		this.maxX = 0;
		this.maxY = 0;
	}
	getClippedPathBoundingBox(pathType = PathType.FILL, transform = null) {
		return Util$1.intersect(this.clipBox, this.getPathBoundingBox(pathType, transform));
	}
};
function putBinaryImageData(ctx, imgData) {
	if (imgData instanceof ImageData) {
		ctx.putImageData(imgData, 0, 0);
		return;
	}
	const height = imgData.height, width = imgData.width;
	const partialChunkHeight = height % FULL_CHUNK_HEIGHT;
	const fullChunks = (height - partialChunkHeight) / FULL_CHUNK_HEIGHT;
	const totalChunks = partialChunkHeight === 0 ? fullChunks : fullChunks + 1;
	const chunkImgData = ctx.createImageData(width, FULL_CHUNK_HEIGHT);
	let srcPos = 0, destPos;
	const src = imgData.data;
	const dest = chunkImgData.data;
	let i, j, thisChunkHeight, elemsInThisChunk;
	if (imgData.kind === util_ImageKind.GRAYSCALE_1BPP) {
		const srcLength = src.byteLength;
		const dest32 = new Uint32Array(dest.buffer, 0, dest.byteLength >> 2);
		const dest32DataLength = dest32.length;
		const fullSrcDiff = width + 7 >> 3;
		const white = 4294967295;
		const black = util_FeatureTest.isLittleEndian ? 4278190080 : 255;
		for (i = 0; i < totalChunks; i++) {
			thisChunkHeight = i < fullChunks ? FULL_CHUNK_HEIGHT : partialChunkHeight;
			destPos = 0;
			for (j = 0; j < thisChunkHeight; j++) {
				const srcDiff = srcLength - srcPos;
				let k = 0;
				const kEnd = srcDiff > fullSrcDiff ? width : srcDiff * 8 - 7;
				const kEndUnrolled = kEnd & -8;
				let mask = 0;
				let srcByte = 0;
				for (; k < kEndUnrolled; k += 8) {
					srcByte = src[srcPos++];
					dest32[destPos++] = srcByte & 128 ? white : black;
					dest32[destPos++] = srcByte & 64 ? white : black;
					dest32[destPos++] = srcByte & 32 ? white : black;
					dest32[destPos++] = srcByte & 16 ? white : black;
					dest32[destPos++] = srcByte & 8 ? white : black;
					dest32[destPos++] = srcByte & 4 ? white : black;
					dest32[destPos++] = srcByte & 2 ? white : black;
					dest32[destPos++] = srcByte & 1 ? white : black;
				}
				for (; k < kEnd; k++) {
					if (mask === 0) {
						srcByte = src[srcPos++];
						mask = 128;
					}
					dest32[destPos++] = srcByte & mask ? white : black;
					mask >>= 1;
				}
			}
			while (destPos < dest32DataLength) dest32[destPos++] = 0;
			ctx.putImageData(chunkImgData, 0, i * FULL_CHUNK_HEIGHT);
		}
	} else if (imgData.kind === util_ImageKind.RGBA_32BPP) {
		j = 0;
		elemsInThisChunk = width * FULL_CHUNK_HEIGHT * 4;
		for (i = 0; i < fullChunks; i++) {
			dest.set(src.subarray(srcPos, srcPos + elemsInThisChunk));
			srcPos += elemsInThisChunk;
			ctx.putImageData(chunkImgData, 0, j);
			j += FULL_CHUNK_HEIGHT;
		}
		if (i < totalChunks) {
			elemsInThisChunk = width * partialChunkHeight * 4;
			dest.set(src.subarray(srcPos, srcPos + elemsInThisChunk));
			ctx.putImageData(chunkImgData, 0, j);
		}
	} else if (imgData.kind === util_ImageKind.RGB_24BPP) {
		thisChunkHeight = FULL_CHUNK_HEIGHT;
		elemsInThisChunk = width * thisChunkHeight;
		for (i = 0; i < totalChunks; i++) {
			if (i >= fullChunks) {
				thisChunkHeight = partialChunkHeight;
				elemsInThisChunk = width * thisChunkHeight;
			}
			destPos = 0;
			for (j = elemsInThisChunk; j--;) {
				dest[destPos++] = src[srcPos++];
				dest[destPos++] = src[srcPos++];
				dest[destPos++] = src[srcPos++];
				dest[destPos++] = 255;
			}
			ctx.putImageData(chunkImgData, 0, i * FULL_CHUNK_HEIGHT);
		}
	} else throw new Error(`bad image kind: ${imgData.kind}`);
}
function putBinaryImageMask(ctx, imgData) {
	if (imgData.bitmap) {
		ctx.drawImage(imgData.bitmap, 0, 0);
		return;
	}
	const height = imgData.height, width = imgData.width;
	const partialChunkHeight = height % FULL_CHUNK_HEIGHT;
	const fullChunks = (height - partialChunkHeight) / FULL_CHUNK_HEIGHT;
	const totalChunks = partialChunkHeight === 0 ? fullChunks : fullChunks + 1;
	const chunkImgData = ctx.createImageData(width, FULL_CHUNK_HEIGHT);
	let srcPos = 0;
	const src = imgData.data;
	const dest = chunkImgData.data;
	for (let i = 0; i < totalChunks; i++) {
		const thisChunkHeight = i < fullChunks ? FULL_CHUNK_HEIGHT : partialChunkHeight;
		({srcPos} = convertBlackAndWhiteToRGBA({
			src,
			srcPos,
			dest,
			width,
			height: thisChunkHeight,
			nonBlackColor: 0
		}));
		ctx.putImageData(chunkImgData, 0, i * FULL_CHUNK_HEIGHT);
	}
}
function copyCtxState(sourceCtx, destCtx) {
	for (const property of [
		"strokeStyle",
		"fillStyle",
		"fillRule",
		"globalAlpha",
		"lineWidth",
		"lineCap",
		"lineJoin",
		"miterLimit",
		"globalCompositeOperation",
		"font",
		"filter"
	]) if (sourceCtx[property] !== void 0) destCtx[property] = sourceCtx[property];
	if (sourceCtx.setLineDash !== void 0) {
		destCtx.setLineDash(sourceCtx.getLineDash());
		destCtx.lineDashOffset = sourceCtx.lineDashOffset;
	}
}
function resetCtxToDefault(ctx) {
	ctx.strokeStyle = ctx.fillStyle = "#000000";
	ctx.fillRule = "nonzero";
	ctx.globalAlpha = 1;
	ctx.lineWidth = 1;
	ctx.lineCap = "butt";
	ctx.lineJoin = "miter";
	ctx.miterLimit = 10;
	ctx.globalCompositeOperation = "source-over";
	ctx.font = "10px sans-serif";
	if (ctx.setLineDash !== void 0) {
		ctx.setLineDash([]);
		ctx.lineDashOffset = 0;
	}
	if (!isNodeJS) {
		const { filter } = ctx;
		if (filter !== "none" && filter !== "") ctx.filter = "none";
	}
}
function getImageSmoothingEnabled(transform, interpolate) {
	if (interpolate) return true;
	const scale = Util$1.singularValueDecompose2dScale(transform);
	scale[0] = Math.fround(scale[0]);
	scale[1] = Math.fround(scale[1]);
	const actualScale = Math.fround((globalThis.devicePixelRatio || 1) * PixelsPerInch$1.PDF_TO_CSS_UNITS);
	return scale[0] <= actualScale && scale[1] <= actualScale;
}
var LINE_CAP_STYLES = [
	"butt",
	"round",
	"square"
];
var LINE_JOIN_STYLES = [
	"miter",
	"round",
	"bevel"
];
var NORMAL_CLIP = {};
var EO_CLIP = {};
var CanvasGraphics = class CanvasGraphics {
	constructor(canvasCtx, commonObjs, objs, canvasFactory, filterFactory, { optionalContentConfig, markedContentStack = null }, annotationCanvasMap, pageColors) {
		this.ctx = canvasCtx;
		this.current = new CanvasExtraState(this.ctx.canvas.width, this.ctx.canvas.height);
		this.stateStack = [];
		this.pendingClip = null;
		this.pendingEOFill = false;
		this.res = null;
		this.xobjs = null;
		this.commonObjs = commonObjs;
		this.objs = objs;
		this.canvasFactory = canvasFactory;
		this.filterFactory = filterFactory;
		this.groupStack = [];
		this.processingType3 = null;
		this.baseTransform = null;
		this.baseTransformStack = [];
		this.groupLevel = 0;
		this.smaskStack = [];
		this.smaskCounter = 0;
		this.tempSMask = null;
		this.suspendedCtx = null;
		this.contentVisible = true;
		this.markedContentStack = markedContentStack || [];
		this.optionalContentConfig = optionalContentConfig;
		this.cachedCanvases = new CachedCanvases(this.canvasFactory);
		this.cachedPatterns = /* @__PURE__ */ new Map();
		this.annotationCanvasMap = annotationCanvasMap;
		this.viewportScale = 1;
		this.outputScaleX = 1;
		this.outputScaleY = 1;
		this.pageColors = pageColors;
		this._cachedScaleForStroking = [-1, 0];
		this._cachedGetSinglePixelWidth = null;
		this._cachedBitmapsMap = /* @__PURE__ */ new Map();
	}
	getObject(data, fallback = null) {
		if (typeof data === "string") return data.startsWith("g_") ? this.commonObjs.get(data) : this.objs.get(data);
		return fallback;
	}
	beginDrawing({ transform, viewport, transparency = false, background = null }) {
		const width = this.ctx.canvas.width;
		const height = this.ctx.canvas.height;
		const savedFillStyle = this.ctx.fillStyle;
		this.ctx.fillStyle = background || "#ffffff";
		this.ctx.fillRect(0, 0, width, height);
		this.ctx.fillStyle = savedFillStyle;
		if (transparency) {
			const transparentCanvas = this.cachedCanvases.getCanvas("transparent", width, height);
			this.compositeCtx = this.ctx;
			this.transparentCanvas = transparentCanvas.canvas;
			this.ctx = transparentCanvas.context;
			this.ctx.save();
			this.ctx.transform(...getCurrentTransform(this.compositeCtx));
		}
		this.ctx.save();
		resetCtxToDefault(this.ctx);
		if (transform) {
			this.ctx.transform(...transform);
			this.outputScaleX = transform[0];
			this.outputScaleY = transform[0];
		}
		this.ctx.transform(...viewport.transform);
		this.viewportScale = viewport.scale;
		this.baseTransform = getCurrentTransform(this.ctx);
	}
	executeOperatorList(operatorList, executionStartIdx, continueCallback, stepper) {
		const argsArray = operatorList.argsArray;
		const fnArray = operatorList.fnArray;
		let i = executionStartIdx || 0;
		const argsArrayLen = argsArray.length;
		if (argsArrayLen === i) return i;
		const chunkOperations = argsArrayLen - i > EXECUTION_STEPS && typeof continueCallback === "function";
		const endTime = chunkOperations ? Date.now() + EXECUTION_TIME : 0;
		let steps = 0;
		const commonObjs = this.commonObjs;
		const objs = this.objs;
		let fnId;
		while (true) {
			if (stepper !== void 0 && i === stepper.nextBreakPoint) {
				stepper.breakIt(i, continueCallback);
				return i;
			}
			fnId = fnArray[i];
			if (fnId !== OPS$1.dependency) this[fnId].apply(this, argsArray[i]);
			else for (const depObjId of argsArray[i]) {
				const objsPool = depObjId.startsWith("g_") ? commonObjs : objs;
				if (!objsPool.has(depObjId)) {
					objsPool.get(depObjId, continueCallback);
					return i;
				}
			}
			i++;
			if (i === argsArrayLen) return i;
			if (chunkOperations && ++steps > EXECUTION_STEPS) {
				if (Date.now() > endTime) {
					continueCallback();
					return i;
				}
				steps = 0;
			}
		}
	}
	#restoreInitialState() {
		while (this.stateStack.length || this.inSMaskMode) this.restore();
		this.current.activeSMask = null;
		this.ctx.restore();
		if (this.transparentCanvas) {
			this.ctx = this.compositeCtx;
			this.ctx.save();
			this.ctx.setTransform(1, 0, 0, 1, 0, 0);
			this.ctx.drawImage(this.transparentCanvas, 0, 0);
			this.ctx.restore();
			this.transparentCanvas = null;
		}
	}
	endDrawing() {
		this.#restoreInitialState();
		this.cachedCanvases.clear();
		this.cachedPatterns.clear();
		for (const cache of this._cachedBitmapsMap.values()) {
			for (const canvas of cache.values()) if (typeof HTMLCanvasElement !== "undefined" && canvas instanceof HTMLCanvasElement) canvas.width = canvas.height = 0;
			cache.clear();
		}
		this._cachedBitmapsMap.clear();
		this.#drawFilter();
	}
	#drawFilter() {
		if (this.pageColors) {
			const hcmFilterId = this.filterFactory.addHCMFilter(this.pageColors.foreground, this.pageColors.background);
			if (hcmFilterId !== "none") {
				const savedFilter = this.ctx.filter;
				this.ctx.filter = hcmFilterId;
				this.ctx.drawImage(this.ctx.canvas, 0, 0);
				this.ctx.filter = savedFilter;
			}
		}
	}
	_scaleImage(img, inverseTransform) {
		const width = img.width ?? img.displayWidth;
		const height = img.height ?? img.displayHeight;
		let widthScale = Math.max(Math.hypot(inverseTransform[0], inverseTransform[1]), 1);
		let heightScale = Math.max(Math.hypot(inverseTransform[2], inverseTransform[3]), 1);
		let paintWidth = width, paintHeight = height;
		let tmpCanvasId = "prescale1";
		let tmpCanvas, tmpCtx;
		while (widthScale > 2 && paintWidth > 1 || heightScale > 2 && paintHeight > 1) {
			let newWidth = paintWidth, newHeight = paintHeight;
			if (widthScale > 2 && paintWidth > 1) {
				newWidth = paintWidth >= 16384 ? Math.floor(paintWidth / 2) - 1 || 1 : Math.ceil(paintWidth / 2);
				widthScale /= paintWidth / newWidth;
			}
			if (heightScale > 2 && paintHeight > 1) {
				newHeight = paintHeight >= 16384 ? Math.floor(paintHeight / 2) - 1 || 1 : Math.ceil(paintHeight) / 2;
				heightScale /= paintHeight / newHeight;
			}
			tmpCanvas = this.cachedCanvases.getCanvas(tmpCanvasId, newWidth, newHeight);
			tmpCtx = tmpCanvas.context;
			tmpCtx.clearRect(0, 0, newWidth, newHeight);
			tmpCtx.drawImage(img, 0, 0, paintWidth, paintHeight, 0, 0, newWidth, newHeight);
			img = tmpCanvas.canvas;
			paintWidth = newWidth;
			paintHeight = newHeight;
			tmpCanvasId = tmpCanvasId === "prescale1" ? "prescale2" : "prescale1";
		}
		return {
			img,
			paintWidth,
			paintHeight
		};
	}
	_createMaskCanvas(img) {
		const ctx = this.ctx;
		const { width, height } = img;
		const fillColor = this.current.fillColor;
		const isPatternFill = this.current.patternFill;
		const currentTransform = getCurrentTransform(ctx);
		let cache, cacheKey, scaled, maskCanvas;
		if ((img.bitmap || img.data) && img.count > 1) {
			const mainKey = img.bitmap || img.data.buffer;
			cacheKey = JSON.stringify(isPatternFill ? currentTransform : [currentTransform.slice(0, 4), fillColor]);
			cache = this._cachedBitmapsMap.get(mainKey);
			if (!cache) {
				cache = /* @__PURE__ */ new Map();
				this._cachedBitmapsMap.set(mainKey, cache);
			}
			const cachedImage = cache.get(cacheKey);
			if (cachedImage && !isPatternFill) return {
				canvas: cachedImage,
				offsetX: Math.round(Math.min(currentTransform[0], currentTransform[2]) + currentTransform[4]),
				offsetY: Math.round(Math.min(currentTransform[1], currentTransform[3]) + currentTransform[5])
			};
			scaled = cachedImage;
		}
		if (!scaled) {
			maskCanvas = this.cachedCanvases.getCanvas("maskCanvas", width, height);
			putBinaryImageMask(maskCanvas.context, img);
		}
		let maskToCanvas = Util$1.transform(currentTransform, [
			1 / width,
			0,
			0,
			-1 / height,
			0,
			0
		]);
		maskToCanvas = Util$1.transform(maskToCanvas, [
			1,
			0,
			0,
			1,
			0,
			-height
		]);
		const [minX, minY, maxX, maxY] = Util$1.getAxialAlignedBoundingBox([
			0,
			0,
			width,
			height
		], maskToCanvas);
		const drawnWidth = Math.round(maxX - minX) || 1;
		const drawnHeight = Math.round(maxY - minY) || 1;
		const fillCanvas = this.cachedCanvases.getCanvas("fillCanvas", drawnWidth, drawnHeight);
		const fillCtx = fillCanvas.context;
		const offsetX = minX;
		const offsetY = minY;
		fillCtx.translate(-offsetX, -offsetY);
		fillCtx.transform(...maskToCanvas);
		if (!scaled) {
			scaled = this._scaleImage(maskCanvas.canvas, getCurrentTransformInverse(fillCtx));
			scaled = scaled.img;
			if (cache && isPatternFill) cache.set(cacheKey, scaled);
		}
		fillCtx.imageSmoothingEnabled = getImageSmoothingEnabled(getCurrentTransform(fillCtx), img.interpolate);
		drawImageAtIntegerCoords(fillCtx, scaled, 0, 0, scaled.width, scaled.height, 0, 0, width, height);
		fillCtx.globalCompositeOperation = "source-in";
		const inverse = Util$1.transform(getCurrentTransformInverse(fillCtx), [
			1,
			0,
			0,
			1,
			-offsetX,
			-offsetY
		]);
		fillCtx.fillStyle = isPatternFill ? fillColor.getPattern(ctx, this, inverse, PathType.FILL) : fillColor;
		fillCtx.fillRect(0, 0, width, height);
		if (cache && !isPatternFill) {
			this.cachedCanvases.delete("fillCanvas");
			cache.set(cacheKey, fillCanvas.canvas);
		}
		return {
			canvas: fillCanvas.canvas,
			offsetX: Math.round(offsetX),
			offsetY: Math.round(offsetY)
		};
	}
	setLineWidth(width) {
		if (width !== this.current.lineWidth) this._cachedScaleForStroking[0] = -1;
		this.current.lineWidth = width;
		this.ctx.lineWidth = width;
	}
	setLineCap(style) {
		this.ctx.lineCap = LINE_CAP_STYLES[style];
	}
	setLineJoin(style) {
		this.ctx.lineJoin = LINE_JOIN_STYLES[style];
	}
	setMiterLimit(limit) {
		this.ctx.miterLimit = limit;
	}
	setDash(dashArray, dashPhase) {
		const ctx = this.ctx;
		if (ctx.setLineDash !== void 0) {
			ctx.setLineDash(dashArray);
			ctx.lineDashOffset = dashPhase;
		}
	}
	setRenderingIntent(intent) {}
	setFlatness(flatness) {}
	setGState(states) {
		for (const [key, value] of states) switch (key) {
			case "LW":
				this.setLineWidth(value);
				break;
			case "LC":
				this.setLineCap(value);
				break;
			case "LJ":
				this.setLineJoin(value);
				break;
			case "ML":
				this.setMiterLimit(value);
				break;
			case "D":
				this.setDash(value[0], value[1]);
				break;
			case "RI":
				this.setRenderingIntent(value);
				break;
			case "FL":
				this.setFlatness(value);
				break;
			case "Font":
				this.setFont(value[0], value[1]);
				break;
			case "CA":
				this.current.strokeAlpha = value;
				break;
			case "ca":
				this.current.fillAlpha = value;
				this.ctx.globalAlpha = value;
				break;
			case "BM":
				this.ctx.globalCompositeOperation = value;
				break;
			case "SMask":
				this.current.activeSMask = value ? this.tempSMask : null;
				this.tempSMask = null;
				this.checkSMaskState();
				break;
			case "TR": this.ctx.filter = this.current.transferMaps = this.filterFactory.addFilter(value);
		}
	}
	get inSMaskMode() {
		return !!this.suspendedCtx;
	}
	checkSMaskState() {
		const inSMaskMode = this.inSMaskMode;
		if (this.current.activeSMask && !inSMaskMode) this.beginSMaskMode();
		else if (!this.current.activeSMask && inSMaskMode) this.endSMaskMode();
	}
	beginSMaskMode() {
		if (this.inSMaskMode) throw new Error("beginSMaskMode called while already in smask mode");
		const drawnWidth = this.ctx.canvas.width;
		const drawnHeight = this.ctx.canvas.height;
		const cacheId = "smaskGroupAt" + this.groupLevel;
		const scratchCanvas = this.cachedCanvases.getCanvas(cacheId, drawnWidth, drawnHeight);
		this.suspendedCtx = this.ctx;
		this.ctx = scratchCanvas.context;
		const ctx = this.ctx;
		ctx.setTransform(...getCurrentTransform(this.suspendedCtx));
		copyCtxState(this.suspendedCtx, ctx);
		mirrorContextOperations(ctx, this.suspendedCtx);
		this.setGState([
			["BM", "source-over"],
			["ca", 1],
			["CA", 1]
		]);
	}
	endSMaskMode() {
		if (!this.inSMaskMode) throw new Error("endSMaskMode called while not in smask mode");
		this.ctx._removeMirroring();
		copyCtxState(this.ctx, this.suspendedCtx);
		this.ctx = this.suspendedCtx;
		this.suspendedCtx = null;
	}
	compose(dirtyBox) {
		if (!this.current.activeSMask) return;
		if (!dirtyBox) dirtyBox = [
			0,
			0,
			this.ctx.canvas.width,
			this.ctx.canvas.height
		];
		else {
			dirtyBox[0] = Math.floor(dirtyBox[0]);
			dirtyBox[1] = Math.floor(dirtyBox[1]);
			dirtyBox[2] = Math.ceil(dirtyBox[2]);
			dirtyBox[3] = Math.ceil(dirtyBox[3]);
		}
		const smask = this.current.activeSMask;
		const suspendedCtx = this.suspendedCtx;
		this.composeSMask(suspendedCtx, smask, this.ctx, dirtyBox);
		this.ctx.save();
		this.ctx.setTransform(1, 0, 0, 1, 0, 0);
		this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
		this.ctx.restore();
	}
	composeSMask(ctx, smask, layerCtx, layerBox) {
		const layerOffsetX = layerBox[0];
		const layerOffsetY = layerBox[1];
		const layerWidth = layerBox[2] - layerOffsetX;
		const layerHeight = layerBox[3] - layerOffsetY;
		if (layerWidth === 0 || layerHeight === 0) return;
		this.genericComposeSMask(smask.context, layerCtx, layerWidth, layerHeight, smask.subtype, smask.backdrop, smask.transferMap, layerOffsetX, layerOffsetY, smask.offsetX, smask.offsetY);
		ctx.save();
		ctx.globalAlpha = 1;
		ctx.globalCompositeOperation = "source-over";
		ctx.setTransform(1, 0, 0, 1, 0, 0);
		ctx.drawImage(layerCtx.canvas, 0, 0);
		ctx.restore();
	}
	genericComposeSMask(maskCtx, layerCtx, width, height, subtype, backdrop, transferMap, layerOffsetX, layerOffsetY, maskOffsetX, maskOffsetY) {
		let maskCanvas = maskCtx.canvas;
		let maskX = layerOffsetX - maskOffsetX;
		let maskY = layerOffsetY - maskOffsetY;
		if (backdrop) {
			const backdropRGB = Util$1.makeHexColor(...backdrop);
			if (maskX < 0 || maskY < 0 || maskX + width > maskCanvas.width || maskY + height > maskCanvas.height) {
				const canvas = this.cachedCanvases.getCanvas("maskExtension", width, height);
				const ctx = canvas.context;
				ctx.drawImage(maskCanvas, -maskX, -maskY);
				ctx.globalCompositeOperation = "destination-atop";
				ctx.fillStyle = backdropRGB;
				ctx.fillRect(0, 0, width, height);
				ctx.globalCompositeOperation = "source-over";
				maskCanvas = canvas.canvas;
				maskX = maskY = 0;
			} else {
				maskCtx.save();
				maskCtx.globalAlpha = 1;
				maskCtx.setTransform(1, 0, 0, 1, 0, 0);
				const clip = new Path2D();
				clip.rect(maskX, maskY, width, height);
				maskCtx.clip(clip);
				maskCtx.globalCompositeOperation = "destination-atop";
				maskCtx.fillStyle = backdropRGB;
				maskCtx.fillRect(maskX, maskY, width, height);
				maskCtx.restore();
			}
		}
		layerCtx.save();
		layerCtx.globalAlpha = 1;
		layerCtx.setTransform(1, 0, 0, 1, 0, 0);
		if (subtype === "Alpha" && transferMap) layerCtx.filter = this.filterFactory.addAlphaFilter(transferMap);
		else if (subtype === "Luminosity") layerCtx.filter = this.filterFactory.addLuminosityFilter(transferMap);
		const clip = new Path2D();
		clip.rect(layerOffsetX, layerOffsetY, width, height);
		layerCtx.clip(clip);
		layerCtx.globalCompositeOperation = "destination-in";
		layerCtx.drawImage(maskCanvas, maskX, maskY, width, height, layerOffsetX, layerOffsetY, width, height);
		layerCtx.restore();
	}
	save() {
		if (this.inSMaskMode) {
			copyCtxState(this.ctx, this.suspendedCtx);
			this.suspendedCtx.save();
		} else this.ctx.save();
		const old = this.current;
		this.stateStack.push(old);
		this.current = old.clone();
	}
	restore() {
		if (this.stateStack.length === 0 && this.inSMaskMode) this.endSMaskMode();
		if (this.stateStack.length !== 0) {
			this.current = this.stateStack.pop();
			if (this.inSMaskMode) {
				this.suspendedCtx.restore();
				copyCtxState(this.suspendedCtx, this.ctx);
			} else this.ctx.restore();
			this.checkSMaskState();
			this.pendingClip = null;
			this._cachedScaleForStroking[0] = -1;
			this._cachedGetSinglePixelWidth = null;
		}
	}
	transform(a, b, c, d, e, f) {
		this.ctx.transform(a, b, c, d, e, f);
		this._cachedScaleForStroking[0] = -1;
		this._cachedGetSinglePixelWidth = null;
	}
	constructPath(ops, args, minMax) {
		const ctx = this.ctx;
		const current = this.current;
		let x = current.x, y = current.y;
		let startX, startY;
		const currentTransform = getCurrentTransform(ctx);
		const isScalingMatrix = currentTransform[0] === 0 && currentTransform[3] === 0 || currentTransform[1] === 0 && currentTransform[2] === 0;
		const minMaxForBezier = isScalingMatrix ? minMax.slice(0) : null;
		for (let i = 0, j = 0, ii = ops.length; i < ii; i++) switch (ops[i] | 0) {
			case OPS$1.rectangle:
				x = args[j++];
				y = args[j++];
				const width = args[j++];
				const height = args[j++];
				const xw = x + width;
				const yh = y + height;
				ctx.moveTo(x, y);
				if (width === 0 || height === 0) ctx.lineTo(xw, yh);
				else {
					ctx.lineTo(xw, y);
					ctx.lineTo(xw, yh);
					ctx.lineTo(x, yh);
				}
				if (!isScalingMatrix) current.updateRectMinMax(currentTransform, [
					x,
					y,
					xw,
					yh
				]);
				ctx.closePath();
				break;
			case OPS$1.moveTo:
				x = args[j++];
				y = args[j++];
				ctx.moveTo(x, y);
				if (!isScalingMatrix) current.updatePathMinMax(currentTransform, x, y);
				break;
			case OPS$1.lineTo:
				x = args[j++];
				y = args[j++];
				ctx.lineTo(x, y);
				if (!isScalingMatrix) current.updatePathMinMax(currentTransform, x, y);
				break;
			case OPS$1.curveTo:
				startX = x;
				startY = y;
				x = args[j + 4];
				y = args[j + 5];
				ctx.bezierCurveTo(args[j], args[j + 1], args[j + 2], args[j + 3], x, y);
				current.updateCurvePathMinMax(currentTransform, startX, startY, args[j], args[j + 1], args[j + 2], args[j + 3], x, y, minMaxForBezier);
				j += 6;
				break;
			case OPS$1.curveTo2:
				startX = x;
				startY = y;
				ctx.bezierCurveTo(x, y, args[j], args[j + 1], args[j + 2], args[j + 3]);
				current.updateCurvePathMinMax(currentTransform, startX, startY, x, y, args[j], args[j + 1], args[j + 2], args[j + 3], minMaxForBezier);
				x = args[j + 2];
				y = args[j + 3];
				j += 4;
				break;
			case OPS$1.curveTo3:
				startX = x;
				startY = y;
				x = args[j + 2];
				y = args[j + 3];
				ctx.bezierCurveTo(args[j], args[j + 1], x, y, x, y);
				current.updateCurvePathMinMax(currentTransform, startX, startY, args[j], args[j + 1], x, y, x, y, minMaxForBezier);
				j += 4;
				break;
			case OPS$1.closePath: ctx.closePath();
		}
		if (isScalingMatrix) current.updateScalingPathMinMax(currentTransform, minMaxForBezier);
		current.setCurrentPoint(x, y);
	}
	closePath() {
		this.ctx.closePath();
	}
	stroke(consumePath = true) {
		const ctx = this.ctx;
		const strokeColor = this.current.strokeColor;
		ctx.globalAlpha = this.current.strokeAlpha;
		if (this.contentVisible) {
			if (typeof strokeColor === "object" && strokeColor?.getPattern) {
				ctx.save();
				ctx.strokeStyle = strokeColor.getPattern(ctx, this, getCurrentTransformInverse(ctx), PathType.STROKE);
				this.rescaleAndStroke(false);
				ctx.restore();
			} else this.rescaleAndStroke(true);
		}
		if (consumePath) this.consumePath(this.current.getClippedPathBoundingBox());
		ctx.globalAlpha = this.current.fillAlpha;
	}
	closeStroke() {
		this.closePath();
		this.stroke();
	}
	fill(consumePath = true) {
		const ctx = this.ctx;
		const fillColor = this.current.fillColor;
		const isPatternFill = this.current.patternFill;
		let needRestore = false;
		if (isPatternFill) {
			ctx.save();
			ctx.fillStyle = fillColor.getPattern(ctx, this, getCurrentTransformInverse(ctx), PathType.FILL);
			needRestore = true;
		}
		const intersect = this.current.getClippedPathBoundingBox();
		if (this.contentVisible && intersect !== null) {
			if (this.pendingEOFill) {
				ctx.fill("evenodd");
				this.pendingEOFill = false;
			} else ctx.fill();
		}
		if (needRestore) ctx.restore();
		if (consumePath) this.consumePath(intersect);
	}
	eoFill() {
		this.pendingEOFill = true;
		this.fill();
	}
	fillStroke() {
		this.fill(false);
		this.stroke(false);
		this.consumePath();
	}
	eoFillStroke() {
		this.pendingEOFill = true;
		this.fillStroke();
	}
	closeFillStroke() {
		this.closePath();
		this.fillStroke();
	}
	closeEOFillStroke() {
		this.pendingEOFill = true;
		this.closePath();
		this.fillStroke();
	}
	endPath() {
		this.consumePath();
	}
	clip() {
		this.pendingClip = NORMAL_CLIP;
	}
	eoClip() {
		this.pendingClip = EO_CLIP;
	}
	beginText() {
		this.current.textMatrix = IDENTITY_MATRIX;
		this.current.textMatrixScale = 1;
		this.current.x = this.current.lineX = 0;
		this.current.y = this.current.lineY = 0;
	}
	endText() {
		const paths = this.pendingTextPaths;
		const ctx = this.ctx;
		if (paths === void 0) {
			ctx.beginPath();
			return;
		}
		const newPath = new Path2D();
		const invTransf = ctx.getTransform().invertSelf();
		for (const { transform, x, y, fontSize, path } of paths) newPath.addPath(path, new DOMMatrix(transform).preMultiplySelf(invTransf).translate(x, y).scale(fontSize, -fontSize));
		ctx.clip(newPath);
		ctx.beginPath();
		delete this.pendingTextPaths;
	}
	setCharSpacing(spacing) {
		this.current.charSpacing = spacing;
	}
	setWordSpacing(spacing) {
		this.current.wordSpacing = spacing;
	}
	setHScale(scale) {
		this.current.textHScale = scale / 100;
	}
	setLeading(leading) {
		this.current.leading = -leading;
	}
	setFont(fontRefName, size) {
		const fontObj = this.commonObjs.get(fontRefName);
		const current = this.current;
		if (!fontObj) throw new Error(`Can't find font for ${fontRefName}`);
		current.fontMatrix = fontObj.fontMatrix || FONT_IDENTITY_MATRIX;
		if (current.fontMatrix[0] === 0 || current.fontMatrix[3] === 0) warn("Invalid font matrix for font " + fontRefName);
		if (size < 0) {
			size = -size;
			current.fontDirection = -1;
		} else current.fontDirection = 1;
		this.current.font = fontObj;
		this.current.fontSize = size;
		if (fontObj.isType3Font) return;
		const name = fontObj.loadedName || "sans-serif";
		const typeface = fontObj.systemFontInfo?.css || `"${name}", ${fontObj.fallbackName}`;
		let bold = "normal";
		if (fontObj.black) bold = "900";
		else if (fontObj.bold) bold = "bold";
		const italic = fontObj.italic ? "italic" : "normal";
		let browserFontSize = size;
		if (size < MIN_FONT_SIZE) browserFontSize = MIN_FONT_SIZE;
		else if (size > MAX_FONT_SIZE) browserFontSize = MAX_FONT_SIZE;
		this.current.fontSizeScale = size / browserFontSize;
		this.ctx.font = `${italic} ${bold} ${browserFontSize}px ${typeface}`;
	}
	setTextRenderingMode(mode) {
		this.current.textRenderingMode = mode;
	}
	setTextRise(rise) {
		this.current.textRise = rise;
	}
	moveText(x, y) {
		this.current.x = this.current.lineX += x;
		this.current.y = this.current.lineY += y;
	}
	setLeadingMoveText(x, y) {
		this.setLeading(-y);
		this.moveText(x, y);
	}
	setTextMatrix(a, b, c, d, e, f) {
		this.current.textMatrix = [
			a,
			b,
			c,
			d,
			e,
			f
		];
		this.current.textMatrixScale = Math.hypot(a, b);
		this.current.x = this.current.lineX = 0;
		this.current.y = this.current.lineY = 0;
	}
	nextLine() {
		this.moveText(0, this.current.leading);
	}
	#getScaledPath(path, currentTransform, transform) {
		const newPath = new Path2D();
		newPath.addPath(path, new DOMMatrix(transform).invertSelf().multiplySelf(currentTransform));
		return newPath;
	}
	paintChar(character, x, y, patternFillTransform, patternStrokeTransform) {
		const ctx = this.ctx;
		const current = this.current;
		const font = current.font;
		const textRenderingMode = current.textRenderingMode;
		const fontSize = current.fontSize / current.fontSizeScale;
		const fillStrokeMode = textRenderingMode & TextRenderingMode.FILL_STROKE_MASK;
		const isAddToPathSet = !!(textRenderingMode & TextRenderingMode.ADD_TO_PATH_FLAG);
		const patternFill = current.patternFill && !font.missingFile;
		const patternStroke = current.patternStroke && !font.missingFile;
		let path;
		if (font.disableFontFace || isAddToPathSet || patternFill || patternStroke) path = font.getPathGenerator(this.commonObjs, character);
		if (font.disableFontFace || patternFill || patternStroke) {
			ctx.save();
			ctx.translate(x, y);
			ctx.scale(fontSize, -fontSize);
			if (fillStrokeMode === TextRenderingMode.FILL || fillStrokeMode === TextRenderingMode.FILL_STROKE) {
				if (patternFillTransform) {
					const currentTransform = ctx.getTransform();
					ctx.setTransform(...patternFillTransform);
					ctx.fill(this.#getScaledPath(path, currentTransform, patternFillTransform));
				} else ctx.fill(path);
			}
			if (fillStrokeMode === TextRenderingMode.STROKE || fillStrokeMode === TextRenderingMode.FILL_STROKE) {
				if (patternStrokeTransform) {
					const currentTransform = ctx.getTransform();
					ctx.setTransform(...patternStrokeTransform);
					ctx.stroke(this.#getScaledPath(path, currentTransform, patternStrokeTransform));
				} else {
					ctx.lineWidth /= fontSize;
					ctx.stroke(path);
				}
			}
			ctx.restore();
		} else {
			if (fillStrokeMode === TextRenderingMode.FILL || fillStrokeMode === TextRenderingMode.FILL_STROKE) ctx.fillText(character, x, y);
			if (fillStrokeMode === TextRenderingMode.STROKE || fillStrokeMode === TextRenderingMode.FILL_STROKE) ctx.strokeText(character, x, y);
		}
		if (isAddToPathSet) (this.pendingTextPaths ||= []).push({
			transform: getCurrentTransform(ctx),
			x,
			y,
			fontSize,
			path
		});
	}
	get isFontSubpixelAAEnabled() {
		const { context: ctx } = this.cachedCanvases.getCanvas("isFontSubpixelAAEnabled", 10, 10);
		ctx.scale(1.5, 1);
		ctx.fillText("I", 0, 10);
		const data = ctx.getImageData(0, 0, 10, 10).data;
		let enabled = false;
		for (let i = 3; i < data.length; i += 4) if (data[i] > 0 && data[i] < 255) {
			enabled = true;
			break;
		}
		return shadow$1(this, "isFontSubpixelAAEnabled", enabled);
	}
	showText(glyphs) {
		const current = this.current;
		const font = current.font;
		if (font.isType3Font) return this.showType3Text(glyphs);
		const fontSize = current.fontSize;
		if (fontSize === 0) return;
		const ctx = this.ctx;
		const fontSizeScale = current.fontSizeScale;
		const charSpacing = current.charSpacing;
		const wordSpacing = current.wordSpacing;
		const fontDirection = current.fontDirection;
		const textHScale = current.textHScale * fontDirection;
		const glyphsLength = glyphs.length;
		const vertical = font.vertical;
		const spacingDir = vertical ? 1 : -1;
		const defaultVMetrics = font.defaultVMetrics;
		const widthAdvanceScale = fontSize * current.fontMatrix[0];
		const simpleFillText = current.textRenderingMode === TextRenderingMode.FILL && !font.disableFontFace && !current.patternFill;
		ctx.save();
		ctx.transform(...current.textMatrix);
		ctx.translate(current.x, current.y + current.textRise);
		if (fontDirection > 0) ctx.scale(textHScale, -1);
		else ctx.scale(textHScale, 1);
		let patternFillTransform, patternStrokeTransform;
		if (current.patternFill) {
			ctx.save();
			const pattern = current.fillColor.getPattern(ctx, this, getCurrentTransformInverse(ctx), PathType.FILL);
			patternFillTransform = getCurrentTransform(ctx);
			ctx.restore();
			ctx.fillStyle = pattern;
		}
		if (current.patternStroke) {
			ctx.save();
			const pattern = current.strokeColor.getPattern(ctx, this, getCurrentTransformInverse(ctx), PathType.STROKE);
			patternStrokeTransform = getCurrentTransform(ctx);
			ctx.restore();
			ctx.strokeStyle = pattern;
		}
		let lineWidth = current.lineWidth;
		const scale = current.textMatrixScale;
		if (scale === 0 || lineWidth === 0) {
			const fillStrokeMode = current.textRenderingMode & TextRenderingMode.FILL_STROKE_MASK;
			if (fillStrokeMode === TextRenderingMode.STROKE || fillStrokeMode === TextRenderingMode.FILL_STROKE) lineWidth = this.getSinglePixelWidth();
		} else lineWidth /= scale;
		if (fontSizeScale !== 1) {
			ctx.scale(fontSizeScale, fontSizeScale);
			lineWidth /= fontSizeScale;
		}
		ctx.lineWidth = lineWidth;
		if (font.isInvalidPDFjsFont) {
			const chars = [];
			let width = 0;
			for (const glyph of glyphs) {
				chars.push(glyph.unicode);
				width += glyph.width;
			}
			ctx.fillText(chars.join(""), 0, 0);
			current.x += width * widthAdvanceScale * textHScale;
			ctx.restore();
			this.compose();
			return;
		}
		let x = 0, i;
		for (i = 0; i < glyphsLength; ++i) {
			const glyph = glyphs[i];
			if (typeof glyph === "number") {
				x += spacingDir * glyph * fontSize / 1e3;
				continue;
			}
			let restoreNeeded = false;
			const spacing = (glyph.isSpace ? wordSpacing : 0) + charSpacing;
			const character = glyph.fontChar;
			const accent = glyph.accent;
			let scaledX, scaledY;
			let width = glyph.width;
			if (vertical) {
				const vmetric = glyph.vmetric || defaultVMetrics;
				const vx = -(glyph.vmetric ? vmetric[1] : width * .5) * widthAdvanceScale;
				const vy = vmetric[2] * widthAdvanceScale;
				width = vmetric ? -vmetric[0] : width;
				scaledX = vx / fontSizeScale;
				scaledY = (x + vy) / fontSizeScale;
			} else {
				scaledX = x / fontSizeScale;
				scaledY = 0;
			}
			if (font.remeasure && width > 0) {
				const measuredWidth = ctx.measureText(character).width * 1e3 / fontSize * fontSizeScale;
				if (width < measuredWidth && this.isFontSubpixelAAEnabled) {
					const characterScaleX = width / measuredWidth;
					restoreNeeded = true;
					ctx.save();
					ctx.scale(characterScaleX, 1);
					scaledX /= characterScaleX;
				} else if (width !== measuredWidth) scaledX += (width - measuredWidth) / 2e3 * fontSize / fontSizeScale;
			}
			if (this.contentVisible && (glyph.isInFont || font.missingFile)) {
				if (simpleFillText && !accent) ctx.fillText(character, scaledX, scaledY);
				else {
					this.paintChar(character, scaledX, scaledY, patternFillTransform, patternStrokeTransform);
					if (accent) {
						const scaledAccentX = scaledX + fontSize * accent.offset.x / fontSizeScale;
						const scaledAccentY = scaledY - fontSize * accent.offset.y / fontSizeScale;
						this.paintChar(accent.fontChar, scaledAccentX, scaledAccentY, patternFillTransform, patternStrokeTransform);
					}
				}
			}
			const charWidth = vertical ? width * widthAdvanceScale - spacing * fontDirection : width * widthAdvanceScale + spacing * fontDirection;
			x += charWidth;
			if (restoreNeeded) ctx.restore();
		}
		if (vertical) current.y -= x;
		else current.x += x * textHScale;
		ctx.restore();
		this.compose();
	}
	showType3Text(glyphs) {
		const ctx = this.ctx;
		const current = this.current;
		const font = current.font;
		const fontSize = current.fontSize;
		const fontDirection = current.fontDirection;
		const spacingDir = font.vertical ? 1 : -1;
		const charSpacing = current.charSpacing;
		const wordSpacing = current.wordSpacing;
		const textHScale = current.textHScale * fontDirection;
		const fontMatrix = current.fontMatrix || FONT_IDENTITY_MATRIX;
		const glyphsLength = glyphs.length;
		const isTextInvisible = current.textRenderingMode === TextRenderingMode.INVISIBLE;
		let i, glyph, width, spacingLength;
		if (isTextInvisible || fontSize === 0) return;
		this._cachedScaleForStroking[0] = -1;
		this._cachedGetSinglePixelWidth = null;
		ctx.save();
		ctx.transform(...current.textMatrix);
		ctx.translate(current.x, current.y);
		ctx.scale(textHScale, fontDirection);
		for (i = 0; i < glyphsLength; ++i) {
			glyph = glyphs[i];
			if (typeof glyph === "number") {
				spacingLength = spacingDir * glyph * fontSize / 1e3;
				this.ctx.translate(spacingLength, 0);
				current.x += spacingLength * textHScale;
				continue;
			}
			const spacing = (glyph.isSpace ? wordSpacing : 0) + charSpacing;
			const operatorList = font.charProcOperatorList[glyph.operatorListId];
			if (!operatorList) {
				warn(`Type3 character "${glyph.operatorListId}" is not available.`);
				continue;
			}
			if (this.contentVisible) {
				this.processingType3 = glyph;
				this.save();
				ctx.scale(fontSize, fontSize);
				ctx.transform(...fontMatrix);
				this.executeOperatorList(operatorList);
				this.restore();
			}
			width = Util$1.applyTransform([glyph.width, 0], fontMatrix)[0] * fontSize + spacing;
			ctx.translate(width, 0);
			current.x += width * textHScale;
		}
		ctx.restore();
		this.processingType3 = null;
	}
	setCharWidth(xWidth, yWidth) {}
	setCharWidthAndBounds(xWidth, yWidth, llx, lly, urx, ury) {
		this.ctx.rect(llx, lly, urx - llx, ury - lly);
		this.ctx.clip();
		this.endPath();
	}
	getColorN_Pattern(IR) {
		let pattern;
		if (IR[0] === "TilingPattern") {
			const color = IR[1];
			const baseTransform = this.baseTransform || getCurrentTransform(this.ctx);
			pattern = new TilingPattern(IR, color, this.ctx, { createCanvasGraphics: (ctx) => new CanvasGraphics(ctx, this.commonObjs, this.objs, this.canvasFactory, this.filterFactory, {
				optionalContentConfig: this.optionalContentConfig,
				markedContentStack: this.markedContentStack
			}) }, baseTransform);
		} else pattern = this._getPattern(IR[1], IR[2]);
		return pattern;
	}
	setStrokeColorN() {
		this.current.strokeColor = this.getColorN_Pattern(arguments);
		this.current.patternStroke = true;
	}
	setFillColorN() {
		this.current.fillColor = this.getColorN_Pattern(arguments);
		this.current.patternFill = true;
	}
	setStrokeRGBColor(r, g, b) {
		this.ctx.strokeStyle = this.current.strokeColor = Util$1.makeHexColor(r, g, b);
		this.current.patternStroke = false;
	}
	setStrokeTransparent() {
		this.ctx.strokeStyle = this.current.strokeColor = "transparent";
		this.current.patternStroke = false;
	}
	setFillRGBColor(r, g, b) {
		this.ctx.fillStyle = this.current.fillColor = Util$1.makeHexColor(r, g, b);
		this.current.patternFill = false;
	}
	setFillTransparent() {
		this.ctx.fillStyle = this.current.fillColor = "transparent";
		this.current.patternFill = false;
	}
	_getPattern(objId, matrix = null) {
		let pattern;
		if (this.cachedPatterns.has(objId)) pattern = this.cachedPatterns.get(objId);
		else {
			pattern = getShadingPattern(this.getObject(objId));
			this.cachedPatterns.set(objId, pattern);
		}
		if (matrix) pattern.matrix = matrix;
		return pattern;
	}
	shadingFill(objId) {
		if (!this.contentVisible) return;
		const ctx = this.ctx;
		this.save();
		ctx.fillStyle = this._getPattern(objId).getPattern(ctx, this, getCurrentTransformInverse(ctx), PathType.SHADING);
		const inv = getCurrentTransformInverse(ctx);
		if (inv) {
			const { width, height } = ctx.canvas;
			const [x0, y0, x1, y1] = Util$1.getAxialAlignedBoundingBox([
				0,
				0,
				width,
				height
			], inv);
			this.ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
		} else this.ctx.fillRect(-1e10, -1e10, 2e10, 2e10);
		this.compose(this.current.getClippedPathBoundingBox());
		this.restore();
	}
	beginInlineImage() {
		unreachable("Should not call beginInlineImage");
	}
	beginImageData() {
		unreachable("Should not call beginImageData");
	}
	paintFormXObjectBegin(matrix, bbox) {
		if (!this.contentVisible) return;
		this.save();
		this.baseTransformStack.push(this.baseTransform);
		if (matrix) this.transform(...matrix);
		this.baseTransform = getCurrentTransform(this.ctx);
		if (bbox) {
			const width = bbox[2] - bbox[0];
			const height = bbox[3] - bbox[1];
			this.ctx.rect(bbox[0], bbox[1], width, height);
			this.current.updateRectMinMax(getCurrentTransform(this.ctx), bbox);
			this.clip();
			this.endPath();
		}
	}
	paintFormXObjectEnd() {
		if (!this.contentVisible) return;
		this.restore();
		this.baseTransform = this.baseTransformStack.pop();
	}
	beginGroup(group) {
		if (!this.contentVisible) return;
		this.save();
		if (this.inSMaskMode) {
			this.endSMaskMode();
			this.current.activeSMask = null;
		}
		const currentCtx = this.ctx;
		if (!group.isolated) info("TODO: Support non-isolated groups.");
		if (group.knockout) warn("Knockout groups not supported.");
		const currentTransform = getCurrentTransform(currentCtx);
		if (group.matrix) currentCtx.transform(...group.matrix);
		if (!group.bbox) throw new Error("Bounding box is required.");
		let bounds = Util$1.getAxialAlignedBoundingBox(group.bbox, getCurrentTransform(currentCtx));
		const canvasBounds = [
			0,
			0,
			currentCtx.canvas.width,
			currentCtx.canvas.height
		];
		bounds = Util$1.intersect(bounds, canvasBounds) || [
			0,
			0,
			0,
			0
		];
		const offsetX = Math.floor(bounds[0]);
		const offsetY = Math.floor(bounds[1]);
		const drawnWidth = Math.max(Math.ceil(bounds[2]) - offsetX, 1);
		const drawnHeight = Math.max(Math.ceil(bounds[3]) - offsetY, 1);
		this.current.startNewPathAndClipBox([
			0,
			0,
			drawnWidth,
			drawnHeight
		]);
		let cacheId = "groupAt" + this.groupLevel;
		if (group.smask) cacheId += "_smask_" + this.smaskCounter++ % 2;
		const scratchCanvas = this.cachedCanvases.getCanvas(cacheId, drawnWidth, drawnHeight);
		const groupCtx = scratchCanvas.context;
		groupCtx.translate(-offsetX, -offsetY);
		groupCtx.transform(...currentTransform);
		if (group.smask) this.smaskStack.push({
			canvas: scratchCanvas.canvas,
			context: groupCtx,
			offsetX,
			offsetY,
			subtype: group.smask.subtype,
			backdrop: group.smask.backdrop,
			transferMap: group.smask.transferMap || null,
			startTransformInverse: null
		});
		else {
			currentCtx.setTransform(1, 0, 0, 1, 0, 0);
			currentCtx.translate(offsetX, offsetY);
			currentCtx.save();
		}
		copyCtxState(currentCtx, groupCtx);
		this.ctx = groupCtx;
		this.setGState([
			["BM", "source-over"],
			["ca", 1],
			["CA", 1]
		]);
		this.groupStack.push(currentCtx);
		this.groupLevel++;
	}
	endGroup(group) {
		if (!this.contentVisible) return;
		this.groupLevel--;
		const groupCtx = this.ctx;
		const ctx = this.groupStack.pop();
		this.ctx = ctx;
		this.ctx.imageSmoothingEnabled = false;
		if (group.smask) {
			this.tempSMask = this.smaskStack.pop();
			this.restore();
		} else {
			this.ctx.restore();
			const currentMtx = getCurrentTransform(this.ctx);
			this.restore();
			this.ctx.save();
			this.ctx.setTransform(...currentMtx);
			const dirtyBox = Util$1.getAxialAlignedBoundingBox([
				0,
				0,
				groupCtx.canvas.width,
				groupCtx.canvas.height
			], currentMtx);
			this.ctx.drawImage(groupCtx.canvas, 0, 0);
			this.ctx.restore();
			this.compose(dirtyBox);
		}
	}
	beginAnnotation(id, rect, transform, matrix, hasOwnCanvas) {
		this.#restoreInitialState();
		resetCtxToDefault(this.ctx);
		this.ctx.save();
		this.save();
		if (this.baseTransform) this.ctx.setTransform(...this.baseTransform);
		if (rect) {
			const width = rect[2] - rect[0];
			const height = rect[3] - rect[1];
			if (hasOwnCanvas && this.annotationCanvasMap) {
				transform = transform.slice();
				transform[4] -= rect[0];
				transform[5] -= rect[1];
				rect = rect.slice();
				rect[0] = rect[1] = 0;
				rect[2] = width;
				rect[3] = height;
				const [scaleX, scaleY] = Util$1.singularValueDecompose2dScale(getCurrentTransform(this.ctx));
				const { viewportScale } = this;
				const canvasWidth = Math.ceil(width * this.outputScaleX * viewportScale);
				const canvasHeight = Math.ceil(height * this.outputScaleY * viewportScale);
				this.annotationCanvas = this.canvasFactory.create(canvasWidth, canvasHeight);
				const { canvas, context } = this.annotationCanvas;
				this.annotationCanvasMap.set(id, canvas);
				this.annotationCanvas.savedCtx = this.ctx;
				this.ctx = context;
				this.ctx.save();
				this.ctx.setTransform(scaleX, 0, 0, -scaleY, 0, height * scaleY);
				resetCtxToDefault(this.ctx);
			} else {
				resetCtxToDefault(this.ctx);
				this.endPath();
				this.ctx.rect(rect[0], rect[1], width, height);
				this.ctx.clip();
				this.ctx.beginPath();
			}
		}
		this.current = new CanvasExtraState(this.ctx.canvas.width, this.ctx.canvas.height);
		this.transform(...transform);
		this.transform(...matrix);
	}
	endAnnotation() {
		if (this.annotationCanvas) {
			this.ctx.restore();
			this.#drawFilter();
			this.ctx = this.annotationCanvas.savedCtx;
			delete this.annotationCanvas.savedCtx;
			delete this.annotationCanvas;
		}
	}
	paintImageMaskXObject(img) {
		if (!this.contentVisible) return;
		const count = img.count;
		img = this.getObject(img.data, img);
		img.count = count;
		const ctx = this.ctx;
		const glyph = this.processingType3;
		if (glyph) {
			if (glyph.compiled === void 0) glyph.compiled = compileType3Glyph(img);
			if (glyph.compiled) {
				glyph.compiled(ctx);
				return;
			}
		}
		const mask = this._createMaskCanvas(img);
		const maskCanvas = mask.canvas;
		ctx.save();
		ctx.setTransform(1, 0, 0, 1, 0, 0);
		ctx.drawImage(maskCanvas, mask.offsetX, mask.offsetY);
		ctx.restore();
		this.compose();
	}
	paintImageMaskXObjectRepeat(img, scaleX, skewX = 0, skewY = 0, scaleY, positions) {
		if (!this.contentVisible) return;
		img = this.getObject(img.data, img);
		const ctx = this.ctx;
		ctx.save();
		const currentTransform = getCurrentTransform(ctx);
		ctx.transform(scaleX, skewX, skewY, scaleY, 0, 0);
		const mask = this._createMaskCanvas(img);
		ctx.setTransform(1, 0, 0, 1, mask.offsetX - currentTransform[4], mask.offsetY - currentTransform[5]);
		for (let i = 0, ii = positions.length; i < ii; i += 2) {
			const trans = Util$1.transform(currentTransform, [
				scaleX,
				skewX,
				skewY,
				scaleY,
				positions[i],
				positions[i + 1]
			]);
			const [x, y] = Util$1.applyTransform([0, 0], trans);
			ctx.drawImage(mask.canvas, x, y);
		}
		ctx.restore();
		this.compose();
	}
	paintImageMaskXObjectGroup(images) {
		if (!this.contentVisible) return;
		const ctx = this.ctx;
		const fillColor = this.current.fillColor;
		const isPatternFill = this.current.patternFill;
		for (const image of images) {
			const { data, width, height, transform } = image;
			const maskCanvas = this.cachedCanvases.getCanvas("maskCanvas", width, height);
			const maskCtx = maskCanvas.context;
			maskCtx.save();
			putBinaryImageMask(maskCtx, this.getObject(data, image));
			maskCtx.globalCompositeOperation = "source-in";
			maskCtx.fillStyle = isPatternFill ? fillColor.getPattern(maskCtx, this, getCurrentTransformInverse(ctx), PathType.FILL) : fillColor;
			maskCtx.fillRect(0, 0, width, height);
			maskCtx.restore();
			ctx.save();
			ctx.transform(...transform);
			ctx.scale(1, -1);
			drawImageAtIntegerCoords(ctx, maskCanvas.canvas, 0, 0, width, height, 0, -1, 1, 1);
			ctx.restore();
		}
		this.compose();
	}
	paintImageXObject(objId) {
		if (!this.contentVisible) return;
		const imgData = this.getObject(objId);
		if (!imgData) {
			warn("Dependent image isn't ready yet");
			return;
		}
		this.paintInlineImageXObject(imgData);
	}
	paintImageXObjectRepeat(objId, scaleX, scaleY, positions) {
		if (!this.contentVisible) return;
		const imgData = this.getObject(objId);
		if (!imgData) {
			warn("Dependent image isn't ready yet");
			return;
		}
		const width = imgData.width;
		const height = imgData.height;
		const map = [];
		for (let i = 0, ii = positions.length; i < ii; i += 2) map.push({
			transform: [
				scaleX,
				0,
				0,
				scaleY,
				positions[i],
				positions[i + 1]
			],
			x: 0,
			y: 0,
			w: width,
			h: height
		});
		this.paintInlineImageXObjectGroup(imgData, map);
	}
	applyTransferMapsToCanvas(ctx) {
		if (this.current.transferMaps !== "none") {
			ctx.filter = this.current.transferMaps;
			ctx.drawImage(ctx.canvas, 0, 0);
			ctx.filter = "none";
		}
		return ctx.canvas;
	}
	applyTransferMapsToBitmap(imgData) {
		if (this.current.transferMaps === "none") return imgData.bitmap;
		const { bitmap, width, height } = imgData;
		const tmpCanvas = this.cachedCanvases.getCanvas("inlineImage", width, height);
		const tmpCtx = tmpCanvas.context;
		tmpCtx.filter = this.current.transferMaps;
		tmpCtx.drawImage(bitmap, 0, 0);
		tmpCtx.filter = "none";
		return tmpCanvas.canvas;
	}
	paintInlineImageXObject(imgData) {
		if (!this.contentVisible) return;
		const width = imgData.width;
		const height = imgData.height;
		const ctx = this.ctx;
		this.save();
		if (!isNodeJS) {
			const { filter } = ctx;
			if (filter !== "none" && filter !== "") ctx.filter = "none";
		}
		ctx.scale(1 / width, -1 / height);
		let imgToPaint;
		if (imgData.bitmap) imgToPaint = this.applyTransferMapsToBitmap(imgData);
		else if (typeof HTMLElement === "function" && imgData instanceof HTMLElement || !imgData.data) imgToPaint = imgData;
		else {
			const tmpCtx = this.cachedCanvases.getCanvas("inlineImage", width, height).context;
			putBinaryImageData(tmpCtx, imgData);
			imgToPaint = this.applyTransferMapsToCanvas(tmpCtx);
		}
		const scaled = this._scaleImage(imgToPaint, getCurrentTransformInverse(ctx));
		ctx.imageSmoothingEnabled = getImageSmoothingEnabled(getCurrentTransform(ctx), imgData.interpolate);
		drawImageAtIntegerCoords(ctx, scaled.img, 0, 0, scaled.paintWidth, scaled.paintHeight, 0, -height, width, height);
		this.compose();
		this.restore();
	}
	paintInlineImageXObjectGroup(imgData, map) {
		if (!this.contentVisible) return;
		const ctx = this.ctx;
		let imgToPaint;
		if (imgData.bitmap) imgToPaint = imgData.bitmap;
		else {
			const w = imgData.width;
			const h = imgData.height;
			const tmpCtx = this.cachedCanvases.getCanvas("inlineImage", w, h).context;
			putBinaryImageData(tmpCtx, imgData);
			imgToPaint = this.applyTransferMapsToCanvas(tmpCtx);
		}
		for (const entry of map) {
			ctx.save();
			ctx.transform(...entry.transform);
			ctx.scale(1, -1);
			drawImageAtIntegerCoords(ctx, imgToPaint, entry.x, entry.y, entry.w, entry.h, 0, -1, 1, 1);
			ctx.restore();
		}
		this.compose();
	}
	paintSolidColorImageMask() {
		if (!this.contentVisible) return;
		this.ctx.fillRect(0, 0, 1, 1);
		this.compose();
	}
	markPoint(tag) {}
	markPointProps(tag, properties) {}
	beginMarkedContent(tag) {
		this.markedContentStack.push({ visible: true });
	}
	beginMarkedContentProps(tag, properties) {
		if (tag === "OC") this.markedContentStack.push({ visible: this.optionalContentConfig.isVisible(properties) });
		else this.markedContentStack.push({ visible: true });
		this.contentVisible = this.isContentVisible();
	}
	endMarkedContent() {
		this.markedContentStack.pop();
		this.contentVisible = this.isContentVisible();
	}
	beginCompat() {}
	endCompat() {}
	consumePath(clipBox) {
		const isEmpty = this.current.isEmptyClip();
		if (this.pendingClip) this.current.updateClipFromPath();
		if (!this.pendingClip) this.compose(clipBox);
		const ctx = this.ctx;
		if (this.pendingClip) {
			if (!isEmpty) {
				if (this.pendingClip === EO_CLIP) ctx.clip("evenodd");
				else ctx.clip();
			}
			this.pendingClip = null;
		}
		this.current.startNewPathAndClipBox(this.current.clipBox);
		ctx.beginPath();
	}
	getSinglePixelWidth() {
		if (!this._cachedGetSinglePixelWidth) {
			const m = getCurrentTransform(this.ctx);
			if (m[1] === 0 && m[2] === 0) this._cachedGetSinglePixelWidth = 1 / Math.min(Math.abs(m[0]), Math.abs(m[3]));
			else {
				const absDet = Math.abs(m[0] * m[3] - m[2] * m[1]);
				const normX = Math.hypot(m[0], m[2]);
				const normY = Math.hypot(m[1], m[3]);
				this._cachedGetSinglePixelWidth = Math.max(normX, normY) / absDet;
			}
		}
		return this._cachedGetSinglePixelWidth;
	}
	getScaleForStroking() {
		if (this._cachedScaleForStroking[0] === -1) {
			const { lineWidth } = this.current;
			const { a, b, c, d } = this.ctx.getTransform();
			let scaleX, scaleY;
			if (b === 0 && c === 0) {
				const normX = Math.abs(a);
				const normY = Math.abs(d);
				if (normX === normY) {
					if (lineWidth === 0) scaleX = scaleY = 1 / normX;
					else {
						const scaledLineWidth = normX * lineWidth;
						scaleX = scaleY = scaledLineWidth < 1 ? 1 / scaledLineWidth : 1;
					}
				} else if (lineWidth === 0) {
					scaleX = 1 / normX;
					scaleY = 1 / normY;
				} else {
					const scaledXLineWidth = normX * lineWidth;
					const scaledYLineWidth = normY * lineWidth;
					scaleX = scaledXLineWidth < 1 ? 1 / scaledXLineWidth : 1;
					scaleY = scaledYLineWidth < 1 ? 1 / scaledYLineWidth : 1;
				}
			} else {
				const absDet = Math.abs(a * d - b * c);
				const normX = Math.hypot(a, b);
				const normY = Math.hypot(c, d);
				if (lineWidth === 0) {
					scaleX = normY / absDet;
					scaleY = normX / absDet;
				} else {
					const baseArea = lineWidth * absDet;
					scaleX = normY > baseArea ? normY / baseArea : 1;
					scaleY = normX > baseArea ? normX / baseArea : 1;
				}
			}
			this._cachedScaleForStroking[0] = scaleX;
			this._cachedScaleForStroking[1] = scaleY;
		}
		return this._cachedScaleForStroking;
	}
	rescaleAndStroke(saveRestore) {
		const { ctx } = this;
		const { lineWidth } = this.current;
		const [scaleX, scaleY] = this.getScaleForStroking();
		ctx.lineWidth = lineWidth || 1;
		if (scaleX === 1 && scaleY === 1) {
			ctx.stroke();
			return;
		}
		const dashes = ctx.getLineDash();
		if (saveRestore) ctx.save();
		ctx.scale(scaleX, scaleY);
		if (dashes.length > 0) {
			const scale = Math.max(scaleX, scaleY);
			ctx.setLineDash(dashes.map((x) => x / scale));
			ctx.lineDashOffset /= scale;
		}
		ctx.stroke();
		if (saveRestore) ctx.restore();
	}
	isContentVisible() {
		for (let i = this.markedContentStack.length - 1; i >= 0; i--) if (!this.markedContentStack[i].visible) return false;
		return true;
	}
};
for (const op in OPS$1) if (CanvasGraphics.prototype[op] !== void 0) CanvasGraphics.prototype[OPS$1[op]] = CanvasGraphics.prototype[op];
var GlobalWorkerOptions$2 = class {
	static #port = null;
	static #src = "";
	static get workerPort() {
		return this.#port;
	}
	static set workerPort(val) {
		if (!(typeof Worker !== "undefined" && val instanceof Worker) && val !== null) throw new Error("Invalid `workerPort` type.");
		this.#port = val;
	}
	static get workerSrc() {
		return this.#src;
	}
	static set workerSrc(val) {
		if (typeof val !== "string") throw new Error("Invalid `workerSrc` type.");
		this.#src = val;
	}
};
var Metadata = class {
	#metadataMap;
	#data;
	constructor({ parsedData, rawData }) {
		this.#metadataMap = parsedData;
		this.#data = rawData;
	}
	getRaw() {
		return this.#data;
	}
	get(name) {
		return this.#metadataMap.get(name) ?? null;
	}
	getAll() {
		return objectFromMap(this.#metadataMap);
	}
	has(name) {
		return this.#metadataMap.has(name);
	}
};
var INTERNAL = Symbol("INTERNAL");
var OptionalContentGroup = class {
	#isDisplay = false;
	#isPrint = false;
	#userSet = false;
	#visible = true;
	constructor(renderingIntent, { name, intent, usage, rbGroups }) {
		this.#isDisplay = !!(renderingIntent & RenderingIntentFlag.DISPLAY);
		this.#isPrint = !!(renderingIntent & RenderingIntentFlag.PRINT);
		this.name = name;
		this.intent = intent;
		this.usage = usage;
		this.rbGroups = rbGroups;
	}
	get visible() {
		if (this.#userSet) return this.#visible;
		if (!this.#visible) return false;
		const { print, view } = this.usage;
		if (this.#isDisplay) return view?.viewState !== "OFF";
		else if (this.#isPrint) return print?.printState !== "OFF";
		return true;
	}
	_setVisible(internal, visible, userSet = false) {
		if (internal !== INTERNAL) unreachable("Internal method `_setVisible` called.");
		this.#userSet = userSet;
		this.#visible = visible;
	}
};
var OptionalContentConfig = class {
	#cachedGetHash = null;
	#groups = /* @__PURE__ */ new Map();
	#initialHash = null;
	#order = null;
	constructor(data, renderingIntent = RenderingIntentFlag.DISPLAY) {
		this.renderingIntent = renderingIntent;
		this.name = null;
		this.creator = null;
		if (data === null) return;
		this.name = data.name;
		this.creator = data.creator;
		this.#order = data.order;
		for (const group of data.groups) this.#groups.set(group.id, new OptionalContentGroup(renderingIntent, group));
		if (data.baseState === "OFF") for (const group of this.#groups.values()) group._setVisible(INTERNAL, false);
		for (const on of data.on) this.#groups.get(on)._setVisible(INTERNAL, true);
		for (const off of data.off) this.#groups.get(off)._setVisible(INTERNAL, false);
		this.#initialHash = this.getHash();
	}
	#evaluateVisibilityExpression(array) {
		const length = array.length;
		if (length < 2) return true;
		const operator = array[0];
		for (let i = 1; i < length; i++) {
			const element = array[i];
			let state;
			if (Array.isArray(element)) state = this.#evaluateVisibilityExpression(element);
			else if (this.#groups.has(element)) state = this.#groups.get(element).visible;
			else {
				warn(`Optional content group not found: ${element}`);
				return true;
			}
			switch (operator) {
				case "And":
					if (!state) return false;
					break;
				case "Or":
					if (state) return true;
					break;
				case "Not": return !state;
				default: return true;
			}
		}
		return operator === "And";
	}
	isVisible(group) {
		if (this.#groups.size === 0) return true;
		if (!group) {
			info("Optional content group not defined.");
			return true;
		}
		if (group.type === "OCG") {
			if (!this.#groups.has(group.id)) {
				warn(`Optional content group not found: ${group.id}`);
				return true;
			}
			return this.#groups.get(group.id).visible;
		} else if (group.type === "OCMD") {
			if (group.expression) return this.#evaluateVisibilityExpression(group.expression);
			if (!group.policy || group.policy === "AnyOn") {
				for (const id of group.ids) {
					if (!this.#groups.has(id)) {
						warn(`Optional content group not found: ${id}`);
						return true;
					}
					if (this.#groups.get(id).visible) return true;
				}
				return false;
			} else if (group.policy === "AllOn") {
				for (const id of group.ids) {
					if (!this.#groups.has(id)) {
						warn(`Optional content group not found: ${id}`);
						return true;
					}
					if (!this.#groups.get(id).visible) return false;
				}
				return true;
			} else if (group.policy === "AnyOff") {
				for (const id of group.ids) {
					if (!this.#groups.has(id)) {
						warn(`Optional content group not found: ${id}`);
						return true;
					}
					if (!this.#groups.get(id).visible) return true;
				}
				return false;
			} else if (group.policy === "AllOff") {
				for (const id of group.ids) {
					if (!this.#groups.has(id)) {
						warn(`Optional content group not found: ${id}`);
						return true;
					}
					if (this.#groups.get(id).visible) return false;
				}
				return true;
			}
			warn(`Unknown optional content policy ${group.policy}.`);
			return true;
		}
		warn(`Unknown group type ${group.type}.`);
		return true;
	}
	setVisibility(id, visible = true, preserveRB = true) {
		const group = this.#groups.get(id);
		if (!group) {
			warn(`Optional content group not found: ${id}`);
			return;
		}
		if (preserveRB && visible && group.rbGroups.length) {
			for (const rbGroup of group.rbGroups) for (const otherId of rbGroup) if (otherId !== id) this.#groups.get(otherId)?._setVisible(INTERNAL, false, true);
		}
		group._setVisible(INTERNAL, !!visible, true);
		this.#cachedGetHash = null;
	}
	setOCGState({ state, preserveRB }) {
		let operator;
		for (const elem of state) {
			switch (elem) {
				case "ON":
				case "OFF":
				case "Toggle":
					operator = elem;
					continue;
			}
			const group = this.#groups.get(elem);
			if (!group) continue;
			switch (operator) {
				case "ON":
					this.setVisibility(elem, true, preserveRB);
					break;
				case "OFF":
					this.setVisibility(elem, false, preserveRB);
					break;
				case "Toggle": this.setVisibility(elem, !group.visible, preserveRB);
			}
		}
		this.#cachedGetHash = null;
	}
	get hasInitialVisibility() {
		return this.#initialHash === null || this.getHash() === this.#initialHash;
	}
	getOrder() {
		if (!this.#groups.size) return null;
		if (this.#order) return this.#order.slice();
		return [...this.#groups.keys()];
	}
	getGroups() {
		return this.#groups.size > 0 ? objectFromMap(this.#groups) : null;
	}
	getGroup(id) {
		return this.#groups.get(id) || null;
	}
	getHash() {
		if (this.#cachedGetHash !== null) return this.#cachedGetHash;
		const hash = new MurmurHash3_64();
		for (const [id, group] of this.#groups) hash.update(`${id}:${group.visible}`);
		return this.#cachedGetHash = hash.hexdigest();
	}
};
var PDFDataTransportStream = class {
	constructor(pdfDataRangeTransport, { disableRange = false, disableStream = false }) {
		assert(pdfDataRangeTransport, "PDFDataTransportStream - missing required \"pdfDataRangeTransport\" argument.");
		const { length, initialData, progressiveDone, contentDispositionFilename } = pdfDataRangeTransport;
		this._queuedChunks = [];
		this._progressiveDone = progressiveDone;
		this._contentDispositionFilename = contentDispositionFilename;
		if (initialData?.length > 0) {
			const buffer = initialData instanceof Uint8Array && initialData.byteLength === initialData.buffer.byteLength ? initialData.buffer : new Uint8Array(initialData).buffer;
			this._queuedChunks.push(buffer);
		}
		this._pdfDataRangeTransport = pdfDataRangeTransport;
		this._isStreamingSupported = !disableStream;
		this._isRangeSupported = !disableRange;
		this._contentLength = length;
		this._fullRequestReader = null;
		this._rangeReaders = [];
		pdfDataRangeTransport.addRangeListener((begin, chunk) => {
			this._onReceiveData({
				begin,
				chunk
			});
		});
		pdfDataRangeTransport.addProgressListener((loaded, total) => {
			this._onProgress({
				loaded,
				total
			});
		});
		pdfDataRangeTransport.addProgressiveReadListener((chunk) => {
			this._onReceiveData({ chunk });
		});
		pdfDataRangeTransport.addProgressiveDoneListener(() => {
			this._onProgressiveDone();
		});
		pdfDataRangeTransport.transportReady();
	}
	_onReceiveData({ begin, chunk }) {
		const buffer = chunk instanceof Uint8Array && chunk.byteLength === chunk.buffer.byteLength ? chunk.buffer : new Uint8Array(chunk).buffer;
		if (begin === void 0) {
			if (this._fullRequestReader) this._fullRequestReader._enqueue(buffer);
			else this._queuedChunks.push(buffer);
		} else assert(this._rangeReaders.some(function(rangeReader) {
			if (rangeReader._begin !== begin) return false;
			rangeReader._enqueue(buffer);
			return true;
		}), "_onReceiveData - no `PDFDataTransportStreamRangeReader` instance found.");
	}
	get _progressiveDataLength() {
		return this._fullRequestReader?._loaded ?? 0;
	}
	_onProgress(evt) {
		if (evt.total === void 0) this._rangeReaders[0]?.onProgress?.({ loaded: evt.loaded });
		else this._fullRequestReader?.onProgress?.({
			loaded: evt.loaded,
			total: evt.total
		});
	}
	_onProgressiveDone() {
		this._fullRequestReader?.progressiveDone();
		this._progressiveDone = true;
	}
	_removeRangeReader(reader) {
		const i = this._rangeReaders.indexOf(reader);
		if (i >= 0) this._rangeReaders.splice(i, 1);
	}
	getFullReader() {
		assert(!this._fullRequestReader, "PDFDataTransportStream.getFullReader can only be called once.");
		const queuedChunks = this._queuedChunks;
		this._queuedChunks = null;
		return new PDFDataTransportStreamReader(this, queuedChunks, this._progressiveDone, this._contentDispositionFilename);
	}
	getRangeReader(begin, end) {
		if (end <= this._progressiveDataLength) return null;
		const reader = new PDFDataTransportStreamRangeReader(this, begin, end);
		this._pdfDataRangeTransport.requestDataRange(begin, end);
		this._rangeReaders.push(reader);
		return reader;
	}
	cancelAllRequests(reason) {
		this._fullRequestReader?.cancel(reason);
		for (const reader of this._rangeReaders.slice(0)) reader.cancel(reason);
		this._pdfDataRangeTransport.abort();
	}
};
var PDFDataTransportStreamReader = class {
	constructor(stream, queuedChunks, progressiveDone = false, contentDispositionFilename = null) {
		this._stream = stream;
		this._done = progressiveDone || false;
		this._filename = isPdfFile$1(contentDispositionFilename) ? contentDispositionFilename : null;
		this._queuedChunks = queuedChunks || [];
		this._loaded = 0;
		for (const chunk of this._queuedChunks) this._loaded += chunk.byteLength;
		this._requests = [];
		this._headersReady = Promise.resolve();
		stream._fullRequestReader = this;
		this.onProgress = null;
	}
	_enqueue(chunk) {
		if (this._done) return;
		if (this._requests.length > 0) this._requests.shift().resolve({
			value: chunk,
			done: false
		});
		else this._queuedChunks.push(chunk);
		this._loaded += chunk.byteLength;
	}
	get headersReady() {
		return this._headersReady;
	}
	get filename() {
		return this._filename;
	}
	get isRangeSupported() {
		return this._stream._isRangeSupported;
	}
	get isStreamingSupported() {
		return this._stream._isStreamingSupported;
	}
	get contentLength() {
		return this._stream._contentLength;
	}
	async read() {
		if (this._queuedChunks.length > 0) return {
			value: this._queuedChunks.shift(),
			done: false
		};
		if (this._done) return {
			value: void 0,
			done: true
		};
		const requestCapability = Promise.withResolvers();
		this._requests.push(requestCapability);
		return requestCapability.promise;
	}
	cancel(reason) {
		this._done = true;
		for (const requestCapability of this._requests) requestCapability.resolve({
			value: void 0,
			done: true
		});
		this._requests.length = 0;
	}
	progressiveDone() {
		if (this._done) return;
		this._done = true;
	}
};
var PDFDataTransportStreamRangeReader = class {
	constructor(stream, begin, end) {
		this._stream = stream;
		this._begin = begin;
		this._end = end;
		this._queuedChunk = null;
		this._requests = [];
		this._done = false;
		this.onProgress = null;
	}
	_enqueue(chunk) {
		if (this._done) return;
		if (this._requests.length === 0) this._queuedChunk = chunk;
		else {
			this._requests.shift().resolve({
				value: chunk,
				done: false
			});
			for (const requestCapability of this._requests) requestCapability.resolve({
				value: void 0,
				done: true
			});
			this._requests.length = 0;
		}
		this._done = true;
		this._stream._removeRangeReader(this);
	}
	get isStreamingSupported() {
		return false;
	}
	async read() {
		if (this._queuedChunk) {
			const chunk = this._queuedChunk;
			this._queuedChunk = null;
			return {
				value: chunk,
				done: false
			};
		}
		if (this._done) return {
			value: void 0,
			done: true
		};
		const requestCapability = Promise.withResolvers();
		this._requests.push(requestCapability);
		return requestCapability.promise;
	}
	cancel(reason) {
		this._done = true;
		for (const requestCapability of this._requests) requestCapability.resolve({
			value: void 0,
			done: true
		});
		this._requests.length = 0;
		this._stream._removeRangeReader(this);
	}
};
function getFilenameFromContentDispositionHeader(contentDisposition) {
	let needsEncodingFixup = true;
	let tmp = toParamRegExp("filename\\*", "i").exec(contentDisposition);
	if (tmp) {
		tmp = tmp[1];
		let filename = rfc2616unquote(tmp);
		filename = unescape(filename);
		filename = rfc5987decode(filename);
		filename = rfc2047decode(filename);
		return fixupEncoding(filename);
	}
	tmp = rfc2231getparam(contentDisposition);
	if (tmp) return fixupEncoding(rfc2047decode(tmp));
	tmp = toParamRegExp("filename", "i").exec(contentDisposition);
	if (tmp) {
		tmp = tmp[1];
		let filename = rfc2616unquote(tmp);
		filename = rfc2047decode(filename);
		return fixupEncoding(filename);
	}
	function toParamRegExp(attributePattern, flags) {
		return new RegExp("(?:^|;)\\s*" + attributePattern + "\\s*=\\s*([^\";\\s][^;\\s]*|\"(?:[^\"\\\\]|\\\\\"?)+\"?)", flags);
	}
	function textdecode(encoding, value) {
		if (encoding) {
			if (!/^[\x00-\xFF]+$/.test(value)) return value;
			try {
				const decoder = new TextDecoder(encoding, { fatal: true });
				const buffer = stringToBytes(value);
				value = decoder.decode(buffer);
				needsEncodingFixup = false;
			} catch {}
		}
		return value;
	}
	function fixupEncoding(value) {
		if (needsEncodingFixup && /[\x80-\xff]/.test(value)) {
			value = textdecode("utf-8", value);
			if (needsEncodingFixup) value = textdecode("iso-8859-1", value);
		}
		return value;
	}
	function rfc2231getparam(contentDispositionStr) {
		const matches = [];
		let match;
		const iter = toParamRegExp("filename\\*((?!0\\d)\\d+)(\\*?)", "ig");
		while ((match = iter.exec(contentDispositionStr)) !== null) {
			let [, n, quot, part] = match;
			n = parseInt(n, 10);
			if (n in matches) {
				if (n === 0) break;
				continue;
			}
			matches[n] = [quot, part];
		}
		const parts = [];
		for (let n = 0; n < matches.length; ++n) {
			if (!(n in matches)) break;
			let [quot, part] = matches[n];
			part = rfc2616unquote(part);
			if (quot) {
				part = unescape(part);
				if (n === 0) part = rfc5987decode(part);
			}
			parts.push(part);
		}
		return parts.join("");
	}
	function rfc2616unquote(value) {
		if (value.startsWith("\"")) {
			const parts = value.slice(1).split("\\\"");
			for (let i = 0; i < parts.length; ++i) {
				const quotindex = parts[i].indexOf("\"");
				if (quotindex !== -1) {
					parts[i] = parts[i].slice(0, quotindex);
					parts.length = i + 1;
				}
				parts[i] = parts[i].replaceAll(/\\(.)/g, "$1");
			}
			value = parts.join("\"");
		}
		return value;
	}
	function rfc5987decode(extvalue) {
		const encodingend = extvalue.indexOf("'");
		if (encodingend === -1) return extvalue;
		return textdecode(extvalue.slice(0, encodingend), extvalue.slice(encodingend + 1).replace(/^[^']*'/, ""));
	}
	function rfc2047decode(value) {
		if (!value.startsWith("=?") || /[\x00-\x19\x80-\xff]/.test(value)) return value;
		return value.replaceAll(/=\?([\w-]*)\?([QqBb])\?((?:[^?]|\?(?!=))*)\?=/g, function(matches, charset, encoding, text) {
			if (encoding === "q" || encoding === "Q") {
				text = text.replaceAll("_", " ");
				text = text.replaceAll(/=([0-9a-fA-F]{2})/g, function(match, hex) {
					return String.fromCharCode(parseInt(hex, 16));
				});
				return textdecode(charset, text);
			}
			try {
				text = atob(text);
			} catch {}
			return textdecode(charset, text);
		});
	}
	return "";
}
function createHeaders(isHttp, httpHeaders) {
	const headers = new Headers();
	if (!isHttp || !httpHeaders || typeof httpHeaders !== "object") return headers;
	for (const key in httpHeaders) {
		const val = httpHeaders[key];
		if (val !== void 0) headers.append(key, val);
	}
	return headers;
}
function getResponseOrigin(url) {
	try {
		return new URL(url).origin;
	} catch {}
	return null;
}
function validateRangeRequestCapabilities({ responseHeaders, isHttp, rangeChunkSize, disableRange }) {
	const returnValues = {
		allowRangeRequests: false,
		suggestedLength: void 0
	};
	const length = parseInt(responseHeaders.get("Content-Length"), 10);
	if (!Number.isInteger(length)) return returnValues;
	returnValues.suggestedLength = length;
	if (length <= 2 * rangeChunkSize) return returnValues;
	if (disableRange || !isHttp) return returnValues;
	if (responseHeaders.get("Accept-Ranges") !== "bytes") return returnValues;
	if ((responseHeaders.get("Content-Encoding") || "identity") !== "identity") return returnValues;
	returnValues.allowRangeRequests = true;
	return returnValues;
}
function extractFilenameFromHeader(responseHeaders) {
	const contentDisposition = responseHeaders.get("Content-Disposition");
	if (contentDisposition) {
		let filename = getFilenameFromContentDispositionHeader(contentDisposition);
		if (filename.includes("%")) try {
			filename = decodeURIComponent(filename);
		} catch {}
		if (isPdfFile$1(filename)) return filename;
	}
	return null;
}
function createResponseStatusError(status, url) {
	if (status === 404 || status === 0 && url.startsWith("file:")) return new MissingPDFException$1("Missing PDF \"" + url + "\".");
	return new UnexpectedResponseException$1(`Unexpected server response (${status}) while retrieving PDF "${url}".`, status);
}
function validateResponseStatus(status) {
	return status === 200 || status === 206;
}
function createFetchOptions(headers, withCredentials, abortController) {
	return {
		method: "GET",
		headers,
		signal: abortController.signal,
		mode: "cors",
		credentials: withCredentials ? "include" : "same-origin",
		redirect: "follow"
	};
}
function getArrayBuffer(val) {
	if (val instanceof Uint8Array) return val.buffer;
	if (val instanceof ArrayBuffer) return val;
	warn(`getArrayBuffer - unexpected data format: ${val}`);
	return new Uint8Array(val).buffer;
}
var PDFFetchStream = class {
	_responseOrigin = null;
	constructor(source) {
		this.source = source;
		this.isHttp = /^https?:/i.test(source.url);
		this.headers = createHeaders(this.isHttp, source.httpHeaders);
		this._fullRequestReader = null;
		this._rangeRequestReaders = [];
	}
	get _progressiveDataLength() {
		return this._fullRequestReader?._loaded ?? 0;
	}
	getFullReader() {
		assert(!this._fullRequestReader, "PDFFetchStream.getFullReader can only be called once.");
		this._fullRequestReader = new PDFFetchStreamReader(this);
		return this._fullRequestReader;
	}
	getRangeReader(begin, end) {
		if (end <= this._progressiveDataLength) return null;
		const reader = new PDFFetchStreamRangeReader(this, begin, end);
		this._rangeRequestReaders.push(reader);
		return reader;
	}
	cancelAllRequests(reason) {
		this._fullRequestReader?.cancel(reason);
		for (const reader of this._rangeRequestReaders.slice(0)) reader.cancel(reason);
	}
};
var PDFFetchStreamReader = class {
	constructor(stream) {
		this._stream = stream;
		this._reader = null;
		this._loaded = 0;
		this._filename = null;
		const source = stream.source;
		this._withCredentials = source.withCredentials || false;
		this._contentLength = source.length;
		this._headersCapability = Promise.withResolvers();
		this._disableRange = source.disableRange || false;
		this._rangeChunkSize = source.rangeChunkSize;
		if (!this._rangeChunkSize && !this._disableRange) this._disableRange = true;
		this._abortController = new AbortController();
		this._isStreamingSupported = !source.disableStream;
		this._isRangeSupported = !source.disableRange;
		const headers = new Headers(stream.headers);
		const url = source.url;
		fetch(url, createFetchOptions(headers, this._withCredentials, this._abortController)).then((response) => {
			stream._responseOrigin = getResponseOrigin(response.url);
			if (!validateResponseStatus(response.status)) throw createResponseStatusError(response.status, url);
			this._reader = response.body.getReader();
			this._headersCapability.resolve();
			const responseHeaders = response.headers;
			const { allowRangeRequests, suggestedLength } = validateRangeRequestCapabilities({
				responseHeaders,
				isHttp: stream.isHttp,
				rangeChunkSize: this._rangeChunkSize,
				disableRange: this._disableRange
			});
			this._isRangeSupported = allowRangeRequests;
			this._contentLength = suggestedLength || this._contentLength;
			this._filename = extractFilenameFromHeader(responseHeaders);
			if (!this._isStreamingSupported && this._isRangeSupported) this.cancel(new AbortException$1("Streaming is disabled."));
		}).catch(this._headersCapability.reject);
		this.onProgress = null;
	}
	get headersReady() {
		return this._headersCapability.promise;
	}
	get filename() {
		return this._filename;
	}
	get contentLength() {
		return this._contentLength;
	}
	get isRangeSupported() {
		return this._isRangeSupported;
	}
	get isStreamingSupported() {
		return this._isStreamingSupported;
	}
	async read() {
		await this._headersCapability.promise;
		const { value, done } = await this._reader.read();
		if (done) return {
			value,
			done
		};
		this._loaded += value.byteLength;
		this.onProgress?.({
			loaded: this._loaded,
			total: this._contentLength
		});
		return {
			value: getArrayBuffer(value),
			done: false
		};
	}
	cancel(reason) {
		this._reader?.cancel(reason);
		this._abortController.abort();
	}
};
var PDFFetchStreamRangeReader = class {
	constructor(stream, begin, end) {
		this._stream = stream;
		this._reader = null;
		this._loaded = 0;
		const source = stream.source;
		this._withCredentials = source.withCredentials || false;
		this._readCapability = Promise.withResolvers();
		this._isStreamingSupported = !source.disableStream;
		this._abortController = new AbortController();
		const headers = new Headers(stream.headers);
		headers.append("Range", `bytes=${begin}-${end - 1}`);
		const url = source.url;
		fetch(url, createFetchOptions(headers, this._withCredentials, this._abortController)).then((response) => {
			const responseOrigin = getResponseOrigin(response.url);
			if (responseOrigin !== stream._responseOrigin) throw new Error(`Expected range response-origin "${responseOrigin}" to match "${stream._responseOrigin}".`);
			if (!validateResponseStatus(response.status)) throw createResponseStatusError(response.status, url);
			this._readCapability.resolve();
			this._reader = response.body.getReader();
		}).catch(this._readCapability.reject);
		this.onProgress = null;
	}
	get isStreamingSupported() {
		return this._isStreamingSupported;
	}
	async read() {
		await this._readCapability.promise;
		const { value, done } = await this._reader.read();
		if (done) return {
			value,
			done
		};
		this._loaded += value.byteLength;
		this.onProgress?.({ loaded: this._loaded });
		return {
			value: getArrayBuffer(value),
			done: false
		};
	}
	cancel(reason) {
		this._reader?.cancel(reason);
		this._abortController.abort();
	}
};
var OK_RESPONSE = 200;
var PARTIAL_CONTENT_RESPONSE = 206;
function network_getArrayBuffer(xhr) {
	const data = xhr.response;
	if (typeof data !== "string") return data;
	return stringToBytes(data).buffer;
}
var NetworkManager = class {
	_responseOrigin = null;
	constructor({ url, httpHeaders, withCredentials }) {
		this.url = url;
		this.isHttp = /^https?:/i.test(url);
		this.headers = createHeaders(this.isHttp, httpHeaders);
		this.withCredentials = withCredentials || false;
		this.currXhrId = 0;
		this.pendingRequests = Object.create(null);
	}
	request(args) {
		const xhr = new XMLHttpRequest();
		const xhrId = this.currXhrId++;
		const pendingRequest = this.pendingRequests[xhrId] = { xhr };
		xhr.open("GET", this.url);
		xhr.withCredentials = this.withCredentials;
		for (const [key, val] of this.headers) xhr.setRequestHeader(key, val);
		if (this.isHttp && "begin" in args && "end" in args) {
			xhr.setRequestHeader("Range", `bytes=${args.begin}-${args.end - 1}`);
			pendingRequest.expectedStatus = PARTIAL_CONTENT_RESPONSE;
		} else pendingRequest.expectedStatus = OK_RESPONSE;
		xhr.responseType = "arraybuffer";
		assert(args.onError, "Expected `onError` callback to be provided.");
		xhr.onerror = () => {
			args.onError(xhr.status);
		};
		xhr.onreadystatechange = this.onStateChange.bind(this, xhrId);
		xhr.onprogress = this.onProgress.bind(this, xhrId);
		pendingRequest.onHeadersReceived = args.onHeadersReceived;
		pendingRequest.onDone = args.onDone;
		pendingRequest.onError = args.onError;
		pendingRequest.onProgress = args.onProgress;
		xhr.send(null);
		return xhrId;
	}
	onProgress(xhrId, evt) {
		const pendingRequest = this.pendingRequests[xhrId];
		if (!pendingRequest) return;
		pendingRequest.onProgress?.(evt);
	}
	onStateChange(xhrId, evt) {
		const pendingRequest = this.pendingRequests[xhrId];
		if (!pendingRequest) return;
		const xhr = pendingRequest.xhr;
		if (xhr.readyState >= 2 && pendingRequest.onHeadersReceived) {
			pendingRequest.onHeadersReceived();
			delete pendingRequest.onHeadersReceived;
		}
		if (xhr.readyState !== 4) return;
		if (!(xhrId in this.pendingRequests)) return;
		delete this.pendingRequests[xhrId];
		if (xhr.status === 0 && this.isHttp) {
			pendingRequest.onError(xhr.status);
			return;
		}
		const xhrStatus = xhr.status || OK_RESPONSE;
		if (!(xhrStatus === OK_RESPONSE && pendingRequest.expectedStatus === PARTIAL_CONTENT_RESPONSE) && xhrStatus !== pendingRequest.expectedStatus) {
			pendingRequest.onError(xhr.status);
			return;
		}
		const chunk = network_getArrayBuffer(xhr);
		if (xhrStatus === PARTIAL_CONTENT_RESPONSE) {
			const rangeHeader = xhr.getResponseHeader("Content-Range");
			const matches = /bytes (\d+)-(\d+)\/(\d+)/.exec(rangeHeader);
			if (matches) pendingRequest.onDone({
				begin: parseInt(matches[1], 10),
				chunk
			});
			else {
				warn(`Missing or invalid "Content-Range" header.`);
				pendingRequest.onError(0);
			}
		} else if (chunk) pendingRequest.onDone({
			begin: 0,
			chunk
		});
		else pendingRequest.onError(xhr.status);
	}
	getRequestXhr(xhrId) {
		return this.pendingRequests[xhrId].xhr;
	}
	isPendingRequest(xhrId) {
		return xhrId in this.pendingRequests;
	}
	abortRequest(xhrId) {
		const xhr = this.pendingRequests[xhrId].xhr;
		delete this.pendingRequests[xhrId];
		xhr.abort();
	}
};
var PDFNetworkStream = class {
	constructor(source) {
		this._source = source;
		this._manager = new NetworkManager(source);
		this._rangeChunkSize = source.rangeChunkSize;
		this._fullRequestReader = null;
		this._rangeRequestReaders = [];
	}
	_onRangeRequestReaderClosed(reader) {
		const i = this._rangeRequestReaders.indexOf(reader);
		if (i >= 0) this._rangeRequestReaders.splice(i, 1);
	}
	getFullReader() {
		assert(!this._fullRequestReader, "PDFNetworkStream.getFullReader can only be called once.");
		this._fullRequestReader = new PDFNetworkStreamFullRequestReader(this._manager, this._source);
		return this._fullRequestReader;
	}
	getRangeReader(begin, end) {
		const reader = new PDFNetworkStreamRangeRequestReader(this._manager, begin, end);
		reader.onClosed = this._onRangeRequestReaderClosed.bind(this);
		this._rangeRequestReaders.push(reader);
		return reader;
	}
	cancelAllRequests(reason) {
		this._fullRequestReader?.cancel(reason);
		for (const reader of this._rangeRequestReaders.slice(0)) reader.cancel(reason);
	}
};
var PDFNetworkStreamFullRequestReader = class {
	constructor(manager, source) {
		this._manager = manager;
		this._url = source.url;
		this._fullRequestId = manager.request({
			onHeadersReceived: this._onHeadersReceived.bind(this),
			onDone: this._onDone.bind(this),
			onError: this._onError.bind(this),
			onProgress: this._onProgress.bind(this)
		});
		this._headersCapability = Promise.withResolvers();
		this._disableRange = source.disableRange || false;
		this._contentLength = source.length;
		this._rangeChunkSize = source.rangeChunkSize;
		if (!this._rangeChunkSize && !this._disableRange) this._disableRange = true;
		this._isStreamingSupported = false;
		this._isRangeSupported = false;
		this._cachedChunks = [];
		this._requests = [];
		this._done = false;
		this._storedError = void 0;
		this._filename = null;
		this.onProgress = null;
	}
	_onHeadersReceived() {
		const fullRequestXhrId = this._fullRequestId;
		const fullRequestXhr = this._manager.getRequestXhr(fullRequestXhrId);
		this._manager._responseOrigin = getResponseOrigin(fullRequestXhr.responseURL);
		const rawResponseHeaders = fullRequestXhr.getAllResponseHeaders();
		const responseHeaders = new Headers(rawResponseHeaders ? rawResponseHeaders.trimStart().replace(/[^\S ]+$/, "").split(/[\r\n]+/).map((x) => {
			const [key, ...val] = x.split(": ");
			return [key, val.join(": ")];
		}) : []);
		const { allowRangeRequests, suggestedLength } = validateRangeRequestCapabilities({
			responseHeaders,
			isHttp: this._manager.isHttp,
			rangeChunkSize: this._rangeChunkSize,
			disableRange: this._disableRange
		});
		if (allowRangeRequests) this._isRangeSupported = true;
		this._contentLength = suggestedLength || this._contentLength;
		this._filename = extractFilenameFromHeader(responseHeaders);
		if (this._isRangeSupported) this._manager.abortRequest(fullRequestXhrId);
		this._headersCapability.resolve();
	}
	_onDone(data) {
		if (data) {
			if (this._requests.length > 0) this._requests.shift().resolve({
				value: data.chunk,
				done: false
			});
			else this._cachedChunks.push(data.chunk);
		}
		this._done = true;
		if (this._cachedChunks.length > 0) return;
		for (const requestCapability of this._requests) requestCapability.resolve({
			value: void 0,
			done: true
		});
		this._requests.length = 0;
	}
	_onError(status) {
		this._storedError = createResponseStatusError(status, this._url);
		this._headersCapability.reject(this._storedError);
		for (const requestCapability of this._requests) requestCapability.reject(this._storedError);
		this._requests.length = 0;
		this._cachedChunks.length = 0;
	}
	_onProgress(evt) {
		this.onProgress?.({
			loaded: evt.loaded,
			total: evt.lengthComputable ? evt.total : this._contentLength
		});
	}
	get filename() {
		return this._filename;
	}
	get isRangeSupported() {
		return this._isRangeSupported;
	}
	get isStreamingSupported() {
		return this._isStreamingSupported;
	}
	get contentLength() {
		return this._contentLength;
	}
	get headersReady() {
		return this._headersCapability.promise;
	}
	async read() {
		await this._headersCapability.promise;
		if (this._storedError) throw this._storedError;
		if (this._cachedChunks.length > 0) return {
			value: this._cachedChunks.shift(),
			done: false
		};
		if (this._done) return {
			value: void 0,
			done: true
		};
		const requestCapability = Promise.withResolvers();
		this._requests.push(requestCapability);
		return requestCapability.promise;
	}
	cancel(reason) {
		this._done = true;
		this._headersCapability.reject(reason);
		for (const requestCapability of this._requests) requestCapability.resolve({
			value: void 0,
			done: true
		});
		this._requests.length = 0;
		if (this._manager.isPendingRequest(this._fullRequestId)) this._manager.abortRequest(this._fullRequestId);
		this._fullRequestReader = null;
	}
};
var PDFNetworkStreamRangeRequestReader = class {
	constructor(manager, begin, end) {
		this._manager = manager;
		this._url = manager.url;
		this._requestId = manager.request({
			begin,
			end,
			onHeadersReceived: this._onHeadersReceived.bind(this),
			onDone: this._onDone.bind(this),
			onError: this._onError.bind(this),
			onProgress: this._onProgress.bind(this)
		});
		this._requests = [];
		this._queuedChunk = null;
		this._done = false;
		this._storedError = void 0;
		this.onProgress = null;
		this.onClosed = null;
	}
	_onHeadersReceived() {
		const responseOrigin = getResponseOrigin(this._manager.getRequestXhr(this._requestId)?.responseURL);
		if (responseOrigin !== this._manager._responseOrigin) {
			this._storedError = /* @__PURE__ */ new Error(`Expected range response-origin "${responseOrigin}" to match "${this._manager._responseOrigin}".`);
			this._onError(0);
		}
	}
	_close() {
		this.onClosed?.(this);
	}
	_onDone(data) {
		const chunk = data.chunk;
		if (this._requests.length > 0) this._requests.shift().resolve({
			value: chunk,
			done: false
		});
		else this._queuedChunk = chunk;
		this._done = true;
		for (const requestCapability of this._requests) requestCapability.resolve({
			value: void 0,
			done: true
		});
		this._requests.length = 0;
		this._close();
	}
	_onError(status) {
		this._storedError ??= createResponseStatusError(status, this._url);
		for (const requestCapability of this._requests) requestCapability.reject(this._storedError);
		this._requests.length = 0;
		this._queuedChunk = null;
	}
	_onProgress(evt) {
		if (!this.isStreamingSupported) this.onProgress?.({ loaded: evt.loaded });
	}
	get isStreamingSupported() {
		return false;
	}
	async read() {
		if (this._storedError) throw this._storedError;
		if (this._queuedChunk !== null) {
			const chunk = this._queuedChunk;
			this._queuedChunk = null;
			return {
				value: chunk,
				done: false
			};
		}
		if (this._done) return {
			value: void 0,
			done: true
		};
		const requestCapability = Promise.withResolvers();
		this._requests.push(requestCapability);
		return requestCapability.promise;
	}
	cancel(reason) {
		this._done = true;
		for (const requestCapability of this._requests) requestCapability.resolve({
			value: void 0,
			done: true
		});
		this._requests.length = 0;
		if (this._manager.isPendingRequest(this._requestId)) this._manager.abortRequest(this._requestId);
		this._close();
	}
};
var urlRegex = /^[a-z][a-z0-9\-+.]+:/i;
function parseUrlOrPath(sourceUrl) {
	if (urlRegex.test(sourceUrl)) return new URL(sourceUrl);
	const url = process.getBuiltinModule("url");
	return new URL(url.pathToFileURL(sourceUrl));
}
var PDFNodeStream = class {
	constructor(source) {
		this.source = source;
		this.url = parseUrlOrPath(source.url);
		assert(this.url.protocol === "file:", "PDFNodeStream only supports file:// URLs.");
		this._fullRequestReader = null;
		this._rangeRequestReaders = [];
	}
	get _progressiveDataLength() {
		return this._fullRequestReader?._loaded ?? 0;
	}
	getFullReader() {
		assert(!this._fullRequestReader, "PDFNodeStream.getFullReader can only be called once.");
		this._fullRequestReader = new PDFNodeStreamFsFullReader(this);
		return this._fullRequestReader;
	}
	getRangeReader(start, end) {
		if (end <= this._progressiveDataLength) return null;
		const rangeReader = new PDFNodeStreamFsRangeReader(this, start, end);
		this._rangeRequestReaders.push(rangeReader);
		return rangeReader;
	}
	cancelAllRequests(reason) {
		this._fullRequestReader?.cancel(reason);
		for (const reader of this._rangeRequestReaders.slice(0)) reader.cancel(reason);
	}
};
var PDFNodeStreamFsFullReader = class {
	constructor(stream) {
		this._url = stream.url;
		this._done = false;
		this._storedError = null;
		this.onProgress = null;
		const source = stream.source;
		this._contentLength = source.length;
		this._loaded = 0;
		this._filename = null;
		this._disableRange = source.disableRange || false;
		this._rangeChunkSize = source.rangeChunkSize;
		if (!this._rangeChunkSize && !this._disableRange) this._disableRange = true;
		this._isStreamingSupported = !source.disableStream;
		this._isRangeSupported = !source.disableRange;
		this._readableStream = null;
		this._readCapability = Promise.withResolvers();
		this._headersCapability = Promise.withResolvers();
		const fs = process.getBuiltinModule("fs");
		fs.promises.lstat(this._url).then((stat) => {
			this._contentLength = stat.size;
			this._setReadableStream(fs.createReadStream(this._url));
			this._headersCapability.resolve();
		}, (error) => {
			if (error.code === "ENOENT") error = new MissingPDFException$1(`Missing PDF "${this._url}".`);
			this._storedError = error;
			this._headersCapability.reject(error);
		});
	}
	get headersReady() {
		return this._headersCapability.promise;
	}
	get filename() {
		return this._filename;
	}
	get contentLength() {
		return this._contentLength;
	}
	get isRangeSupported() {
		return this._isRangeSupported;
	}
	get isStreamingSupported() {
		return this._isStreamingSupported;
	}
	async read() {
		await this._readCapability.promise;
		if (this._done) return {
			value: void 0,
			done: true
		};
		if (this._storedError) throw this._storedError;
		const chunk = this._readableStream.read();
		if (chunk === null) {
			this._readCapability = Promise.withResolvers();
			return this.read();
		}
		this._loaded += chunk.length;
		this.onProgress?.({
			loaded: this._loaded,
			total: this._contentLength
		});
		return {
			value: new Uint8Array(chunk).buffer,
			done: false
		};
	}
	cancel(reason) {
		if (!this._readableStream) {
			this._error(reason);
			return;
		}
		this._readableStream.destroy(reason);
	}
	_error(reason) {
		this._storedError = reason;
		this._readCapability.resolve();
	}
	_setReadableStream(readableStream) {
		this._readableStream = readableStream;
		readableStream.on("readable", () => {
			this._readCapability.resolve();
		});
		readableStream.on("end", () => {
			readableStream.destroy();
			this._done = true;
			this._readCapability.resolve();
		});
		readableStream.on("error", (reason) => {
			this._error(reason);
		});
		if (!this._isStreamingSupported && this._isRangeSupported) this._error(new AbortException$1("streaming is disabled"));
		if (this._storedError) this._readableStream.destroy(this._storedError);
	}
};
var PDFNodeStreamFsRangeReader = class {
	constructor(stream, start, end) {
		this._url = stream.url;
		this._done = false;
		this._storedError = null;
		this.onProgress = null;
		this._loaded = 0;
		this._readableStream = null;
		this._readCapability = Promise.withResolvers();
		const source = stream.source;
		this._isStreamingSupported = !source.disableStream;
		const fs = process.getBuiltinModule("fs");
		this._setReadableStream(fs.createReadStream(this._url, {
			start,
			end: end - 1
		}));
	}
	get isStreamingSupported() {
		return this._isStreamingSupported;
	}
	async read() {
		await this._readCapability.promise;
		if (this._done) return {
			value: void 0,
			done: true
		};
		if (this._storedError) throw this._storedError;
		const chunk = this._readableStream.read();
		if (chunk === null) {
			this._readCapability = Promise.withResolvers();
			return this.read();
		}
		this._loaded += chunk.length;
		this.onProgress?.({ loaded: this._loaded });
		return {
			value: new Uint8Array(chunk).buffer,
			done: false
		};
	}
	cancel(reason) {
		if (!this._readableStream) {
			this._error(reason);
			return;
		}
		this._readableStream.destroy(reason);
	}
	_error(reason) {
		this._storedError = reason;
		this._readCapability.resolve();
	}
	_setReadableStream(readableStream) {
		this._readableStream = readableStream;
		readableStream.on("readable", () => {
			this._readCapability.resolve();
		});
		readableStream.on("end", () => {
			readableStream.destroy();
			this._done = true;
			this._readCapability.resolve();
		});
		readableStream.on("error", (reason) => {
			this._error(reason);
		});
		if (this._storedError) this._readableStream.destroy(this._storedError);
	}
};
var MAX_TEXT_DIVS_TO_RENDER = 1e5;
var DEFAULT_FONT_SIZE = 30;
var DEFAULT_FONT_ASCENT = .8;
var TextLayer$1 = class TextLayer$1 {
	#capability = Promise.withResolvers();
	#container = null;
	#disableProcessItems = false;
	#fontInspectorEnabled = !!globalThis.FontInspector?.enabled;
	#lang = null;
	#layoutTextParams = null;
	#pageHeight = 0;
	#pageWidth = 0;
	#reader = null;
	#rootContainer = null;
	#rotation = 0;
	#scale = 0;
	#styleCache = Object.create(null);
	#textContentItemsStr = [];
	#textContentSource = null;
	#textDivs = [];
	#textDivProperties = /* @__PURE__ */ new WeakMap();
	#transform = null;
	static #ascentCache = /* @__PURE__ */ new Map();
	static #canvasContexts = /* @__PURE__ */ new Map();
	static #canvasCtxFonts = /* @__PURE__ */ new WeakMap();
	static #minFontSize = null;
	static #pendingTextLayers = /* @__PURE__ */ new Set();
	constructor({ textContentSource, container, viewport }) {
		if (textContentSource instanceof ReadableStream) this.#textContentSource = textContentSource;
		else if (typeof textContentSource === "object") this.#textContentSource = new ReadableStream({ start(controller) {
			controller.enqueue(textContentSource);
			controller.close();
		} });
		else throw new Error("No \"textContentSource\" parameter specified.");
		this.#container = this.#rootContainer = container;
		this.#scale = viewport.scale * (globalThis.devicePixelRatio || 1);
		this.#rotation = viewport.rotation;
		this.#layoutTextParams = {
			div: null,
			properties: null,
			ctx: null
		};
		const { pageWidth, pageHeight, pageX, pageY } = viewport.rawDims;
		this.#transform = [
			1,
			0,
			0,
			-1,
			-pageX,
			pageY + pageHeight
		];
		this.#pageWidth = pageWidth;
		this.#pageHeight = pageHeight;
		TextLayer$1.#ensureMinFontSizeComputed();
		setLayerDimensions$1(container, viewport);
		this.#capability.promise.finally(() => {
			TextLayer$1.#pendingTextLayers.delete(this);
			this.#layoutTextParams = null;
			this.#styleCache = null;
		}).catch(() => {});
	}
	static get fontFamilyMap() {
		const { isWindows, isFirefox } = util_FeatureTest.platform;
		return shadow$1(this, "fontFamilyMap", /* @__PURE__ */ new Map([["sans-serif", `${isWindows && isFirefox ? "Calibri, " : ""}sans-serif`], ["monospace", `${isWindows && isFirefox ? "Lucida Console, " : ""}monospace`]]));
	}
	render() {
		const pump = () => {
			this.#reader.read().then(({ value, done }) => {
				if (done) {
					this.#capability.resolve();
					return;
				}
				this.#lang ??= value.lang;
				Object.assign(this.#styleCache, value.styles);
				this.#processItems(value.items);
				pump();
			}, this.#capability.reject);
		};
		this.#reader = this.#textContentSource.getReader();
		TextLayer$1.#pendingTextLayers.add(this);
		pump();
		return this.#capability.promise;
	}
	update({ viewport, onBefore = null }) {
		const scale = viewport.scale * (globalThis.devicePixelRatio || 1);
		const rotation = viewport.rotation;
		if (rotation !== this.#rotation) {
			onBefore?.();
			this.#rotation = rotation;
			setLayerDimensions$1(this.#rootContainer, { rotation });
		}
		if (scale !== this.#scale) {
			onBefore?.();
			this.#scale = scale;
			const params = {
				div: null,
				properties: null,
				ctx: TextLayer$1.#getCtx(this.#lang)
			};
			for (const div of this.#textDivs) {
				params.properties = this.#textDivProperties.get(div);
				params.div = div;
				this.#layout(params);
			}
		}
	}
	cancel() {
		const abortEx = new AbortException$1("TextLayer task cancelled.");
		this.#reader?.cancel(abortEx).catch(() => {});
		this.#reader = null;
		this.#capability.reject(abortEx);
	}
	get textDivs() {
		return this.#textDivs;
	}
	get textContentItemsStr() {
		return this.#textContentItemsStr;
	}
	#processItems(items) {
		if (this.#disableProcessItems) return;
		this.#layoutTextParams.ctx ??= TextLayer$1.#getCtx(this.#lang);
		const textDivs = this.#textDivs, textContentItemsStr = this.#textContentItemsStr;
		for (const item of items) {
			if (textDivs.length > MAX_TEXT_DIVS_TO_RENDER) {
				warn("Ignoring additional textDivs for performance reasons.");
				this.#disableProcessItems = true;
				return;
			}
			if (item.str === void 0) {
				if (item.type === "beginMarkedContentProps" || item.type === "beginMarkedContent") {
					const parent = this.#container;
					this.#container = document.createElement("span");
					this.#container.classList.add("markedContent");
					if (item.id !== null) this.#container.setAttribute("id", `${item.id}`);
					parent.append(this.#container);
				} else if (item.type === "endMarkedContent") this.#container = this.#container.parentNode;
				continue;
			}
			textContentItemsStr.push(item.str);
			this.#appendText(item);
		}
	}
	#appendText(geom) {
		const textDiv = document.createElement("span");
		const textDivProperties = {
			angle: 0,
			canvasWidth: 0,
			hasText: geom.str !== "",
			hasEOL: geom.hasEOL,
			fontSize: 0
		};
		this.#textDivs.push(textDiv);
		const tx = Util$1.transform(this.#transform, geom.transform);
		let angle = Math.atan2(tx[1], tx[0]);
		const style = this.#styleCache[geom.fontName];
		if (style.vertical) angle += Math.PI / 2;
		let fontFamily = this.#fontInspectorEnabled && style.fontSubstitution || style.fontFamily;
		fontFamily = TextLayer$1.fontFamilyMap.get(fontFamily) || fontFamily;
		const fontHeight = Math.hypot(tx[2], tx[3]);
		const fontAscent = fontHeight * TextLayer$1.#getAscent(fontFamily, this.#lang);
		let left, top;
		if (angle === 0) {
			left = tx[4];
			top = tx[5] - fontAscent;
		} else {
			left = tx[4] + fontAscent * Math.sin(angle);
			top = tx[5] - fontAscent * Math.cos(angle);
		}
		const scaleFactorStr = "calc(var(--scale-factor)*";
		const divStyle = textDiv.style;
		if (this.#container === this.#rootContainer) {
			divStyle.left = `${(100 * left / this.#pageWidth).toFixed(2)}%`;
			divStyle.top = `${(100 * top / this.#pageHeight).toFixed(2)}%`;
		} else {
			divStyle.left = `${scaleFactorStr}${left.toFixed(2)}px)`;
			divStyle.top = `${scaleFactorStr}${top.toFixed(2)}px)`;
		}
		divStyle.fontSize = `${scaleFactorStr}${(TextLayer$1.#minFontSize * fontHeight).toFixed(2)}px)`;
		divStyle.fontFamily = fontFamily;
		textDivProperties.fontSize = fontHeight;
		textDiv.setAttribute("role", "presentation");
		textDiv.textContent = geom.str;
		textDiv.dir = geom.dir;
		if (this.#fontInspectorEnabled) textDiv.dataset.fontName = style.fontSubstitutionLoadedName || geom.fontName;
		if (angle !== 0) textDivProperties.angle = angle * (180 / Math.PI);
		let shouldScaleText = false;
		if (geom.str.length > 1) shouldScaleText = true;
		else if (geom.str !== " " && geom.transform[0] !== geom.transform[3]) {
			const absScaleX = Math.abs(geom.transform[0]), absScaleY = Math.abs(geom.transform[3]);
			if (absScaleX !== absScaleY && Math.max(absScaleX, absScaleY) / Math.min(absScaleX, absScaleY) > 1.5) shouldScaleText = true;
		}
		if (shouldScaleText) textDivProperties.canvasWidth = style.vertical ? geom.height : geom.width;
		this.#textDivProperties.set(textDiv, textDivProperties);
		this.#layoutTextParams.div = textDiv;
		this.#layoutTextParams.properties = textDivProperties;
		this.#layout(this.#layoutTextParams);
		if (textDivProperties.hasText) this.#container.append(textDiv);
		if (textDivProperties.hasEOL) {
			const br = document.createElement("br");
			br.setAttribute("role", "presentation");
			this.#container.append(br);
		}
	}
	#layout(params) {
		const { div, properties, ctx } = params;
		const { style } = div;
		let transform = "";
		if (TextLayer$1.#minFontSize > 1) transform = `scale(${1 / TextLayer$1.#minFontSize})`;
		if (properties.canvasWidth !== 0 && properties.hasText) {
			const { fontFamily } = style;
			const { canvasWidth, fontSize } = properties;
			TextLayer$1.#ensureCtxFont(ctx, fontSize * this.#scale, fontFamily);
			const { width } = ctx.measureText(div.textContent);
			if (width > 0) transform = `scaleX(${canvasWidth * this.#scale / width}) ${transform}`;
		}
		if (properties.angle !== 0) transform = `rotate(${properties.angle}deg) ${transform}`;
		if (transform.length > 0) style.transform = transform;
	}
	static cleanup() {
		if (this.#pendingTextLayers.size > 0) return;
		this.#ascentCache.clear();
		for (const { canvas } of this.#canvasContexts.values()) canvas.remove();
		this.#canvasContexts.clear();
	}
	static #getCtx(lang = null) {
		let ctx = this.#canvasContexts.get(lang ||= "");
		if (!ctx) {
			const canvas = document.createElement("canvas");
			canvas.className = "hiddenCanvasElement";
			canvas.lang = lang;
			document.body.append(canvas);
			ctx = canvas.getContext("2d", {
				alpha: false,
				willReadFrequently: true
			});
			this.#canvasContexts.set(lang, ctx);
			this.#canvasCtxFonts.set(ctx, {
				size: 0,
				family: ""
			});
		}
		return ctx;
	}
	static #ensureCtxFont(ctx, size, family) {
		const cached = this.#canvasCtxFonts.get(ctx);
		if (size === cached.size && family === cached.family) return;
		ctx.font = `${size}px ${family}`;
		cached.size = size;
		cached.family = family;
	}
	static #ensureMinFontSizeComputed() {
		if (this.#minFontSize !== null) return;
		const div = document.createElement("div");
		div.style.opacity = 0;
		div.style.lineHeight = 1;
		div.style.fontSize = "1px";
		div.style.position = "absolute";
		div.textContent = "X";
		document.body.append(div);
		this.#minFontSize = div.getBoundingClientRect().height;
		div.remove();
	}
	static #getAscent(fontFamily, lang) {
		const cachedAscent = this.#ascentCache.get(fontFamily);
		if (cachedAscent) return cachedAscent;
		const ctx = this.#getCtx(lang);
		ctx.canvas.width = ctx.canvas.height = DEFAULT_FONT_SIZE;
		this.#ensureCtxFont(ctx, DEFAULT_FONT_SIZE, fontFamily);
		const metrics = ctx.measureText("");
		let ascent = metrics.fontBoundingBoxAscent;
		let descent = Math.abs(metrics.fontBoundingBoxDescent);
		if (ascent) {
			const ratio = ascent / (ascent + descent);
			this.#ascentCache.set(fontFamily, ratio);
			ctx.canvas.width = ctx.canvas.height = 0;
			return ratio;
		}
		ctx.strokeStyle = "red";
		ctx.clearRect(0, 0, DEFAULT_FONT_SIZE, DEFAULT_FONT_SIZE);
		ctx.strokeText("g", 0, 0);
		let pixels = ctx.getImageData(0, 0, DEFAULT_FONT_SIZE, DEFAULT_FONT_SIZE).data;
		descent = 0;
		for (let i = pixels.length - 1 - 3; i >= 0; i -= 4) if (pixels[i] > 0) {
			descent = Math.ceil(i / 4 / DEFAULT_FONT_SIZE);
			break;
		}
		ctx.clearRect(0, 0, DEFAULT_FONT_SIZE, DEFAULT_FONT_SIZE);
		ctx.strokeText("A", 0, DEFAULT_FONT_SIZE);
		pixels = ctx.getImageData(0, 0, DEFAULT_FONT_SIZE, DEFAULT_FONT_SIZE).data;
		ascent = 0;
		for (let i = 0, ii = pixels.length; i < ii; i += 4) if (pixels[i] > 0) {
			ascent = DEFAULT_FONT_SIZE - Math.floor(i / 4 / DEFAULT_FONT_SIZE);
			break;
		}
		ctx.canvas.width = ctx.canvas.height = 0;
		const ratio = ascent ? ascent / (ascent + descent) : DEFAULT_FONT_ASCENT;
		this.#ascentCache.set(fontFamily, ratio);
		return ratio;
	}
};
var XfaText = class XfaText {
	static textContent(xfa) {
		const items = [];
		const output = {
			items,
			styles: Object.create(null)
		};
		function walk(node) {
			if (!node) return;
			let str = null;
			const name = node.name;
			if (name === "#text") str = node.value;
			else if (!XfaText.shouldBuildText(name)) return;
			else if (node?.attributes?.textContent) str = node.attributes.textContent;
			else if (node.value) str = node.value;
			if (str !== null) items.push({ str });
			if (!node.children) return;
			for (const child of node.children) walk(child);
		}
		walk(xfa);
		return output;
	}
	static shouldBuildText(name) {
		return !(name === "textarea" || name === "input" || name === "option" || name === "select");
	}
};
var DEFAULT_RANGE_CHUNK_SIZE = 65536;
var RENDERING_CANCELLED_TIMEOUT = 100;
var DELAYED_CLEANUP_TIMEOUT = 5e3;
var DefaultCanvasFactory = isNodeJS ? NodeCanvasFactory : DOMCanvasFactory;
var DefaultCMapReaderFactory = isNodeJS ? NodeCMapReaderFactory : DOMCMapReaderFactory;
var DefaultFilterFactory = isNodeJS ? NodeFilterFactory : DOMFilterFactory;
var DefaultStandardFontDataFactory = isNodeJS ? NodeStandardFontDataFactory : DOMStandardFontDataFactory;
function getDocument$2(src = {}) {
	if (typeof src === "string" || src instanceof URL) src = { url: src };
	else if (src instanceof ArrayBuffer || ArrayBuffer.isView(src)) src = { data: src };
	const task = new PDFDocumentLoadingTask();
	const { docId } = task;
	const url = src.url ? getUrlProp(src.url) : null;
	const data = src.data ? getDataProp(src.data) : null;
	const httpHeaders = src.httpHeaders || null;
	const withCredentials = src.withCredentials === true;
	const password = src.password ?? null;
	const rangeTransport = src.range instanceof PDFDataRangeTransport$1 ? src.range : null;
	const rangeChunkSize = Number.isInteger(src.rangeChunkSize) && src.rangeChunkSize > 0 ? src.rangeChunkSize : DEFAULT_RANGE_CHUNK_SIZE;
	let worker = src.worker instanceof PDFWorker$1 ? src.worker : null;
	const verbosity = src.verbosity;
	const docBaseUrl = typeof src.docBaseUrl === "string" && !isDataScheme$1(src.docBaseUrl) ? src.docBaseUrl : null;
	const cMapUrl = typeof src.cMapUrl === "string" ? src.cMapUrl : null;
	const cMapPacked = src.cMapPacked !== false;
	const CMapReaderFactory = src.CMapReaderFactory || DefaultCMapReaderFactory;
	const standardFontDataUrl = typeof src.standardFontDataUrl === "string" ? src.standardFontDataUrl : null;
	const StandardFontDataFactory = src.StandardFontDataFactory || DefaultStandardFontDataFactory;
	const ignoreErrors = src.stopAtErrors !== true;
	const maxImageSize = Number.isInteger(src.maxImageSize) && src.maxImageSize > -1 ? src.maxImageSize : -1;
	const isEvalSupported = src.isEvalSupported !== false;
	const isOffscreenCanvasSupported = typeof src.isOffscreenCanvasSupported === "boolean" ? src.isOffscreenCanvasSupported : !isNodeJS;
	const isImageDecoderSupported = typeof src.isImageDecoderSupported === "boolean" ? src.isImageDecoderSupported : !isNodeJS && (util_FeatureTest.platform.isFirefox || !globalThis.chrome);
	const canvasMaxAreaInBytes = Number.isInteger(src.canvasMaxAreaInBytes) ? src.canvasMaxAreaInBytes : -1;
	const disableFontFace = typeof src.disableFontFace === "boolean" ? src.disableFontFace : isNodeJS;
	const fontExtraProperties = src.fontExtraProperties === true;
	const enableXfa = src.enableXfa === true;
	const ownerDocument = src.ownerDocument || globalThis.document;
	const disableRange = src.disableRange === true;
	const disableStream = src.disableStream === true;
	const disableAutoFetch = src.disableAutoFetch === true;
	const pdfBug = src.pdfBug === true;
	const CanvasFactory = src.CanvasFactory || DefaultCanvasFactory;
	const FilterFactory = src.FilterFactory || DefaultFilterFactory;
	const enableHWA = src.enableHWA === true;
	const length = rangeTransport ? rangeTransport.length : src.length ?? NaN;
	const useSystemFonts = typeof src.useSystemFonts === "boolean" ? src.useSystemFonts : !isNodeJS && !disableFontFace;
	const useWorkerFetch = typeof src.useWorkerFetch === "boolean" ? src.useWorkerFetch : CMapReaderFactory === DOMCMapReaderFactory && StandardFontDataFactory === DOMStandardFontDataFactory && cMapUrl && standardFontDataUrl && isValidFetchUrl(cMapUrl, document.baseURI) && isValidFetchUrl(standardFontDataUrl, document.baseURI);
	const styleElement = null;
	setVerbosityLevel(verbosity);
	const transportFactory = {
		canvasFactory: new CanvasFactory({
			ownerDocument,
			enableHWA
		}),
		filterFactory: new FilterFactory({
			docId,
			ownerDocument
		}),
		cMapReaderFactory: useWorkerFetch ? null : new CMapReaderFactory({
			baseUrl: cMapUrl,
			isCompressed: cMapPacked
		}),
		standardFontDataFactory: useWorkerFetch ? null : new StandardFontDataFactory({ baseUrl: standardFontDataUrl })
	};
	if (!worker) {
		const workerParams = {
			verbosity,
			port: GlobalWorkerOptions$2.workerPort
		};
		worker = workerParams.port ? PDFWorker$1.fromPort(workerParams) : new PDFWorker$1(workerParams);
		task._worker = worker;
	}
	const docParams = {
		docId,
		apiVersion: "4.10.38",
		data,
		password,
		disableAutoFetch,
		rangeChunkSize,
		length,
		docBaseUrl,
		enableXfa,
		evaluatorOptions: {
			maxImageSize,
			disableFontFace,
			ignoreErrors,
			isEvalSupported,
			isOffscreenCanvasSupported,
			isImageDecoderSupported,
			canvasMaxAreaInBytes,
			fontExtraProperties,
			useSystemFonts,
			cMapUrl: useWorkerFetch ? cMapUrl : null,
			standardFontDataUrl: useWorkerFetch ? standardFontDataUrl : null
		}
	};
	const transportParams = {
		disableFontFace,
		fontExtraProperties,
		ownerDocument,
		pdfBug,
		styleElement,
		loadingParams: {
			disableAutoFetch,
			enableXfa
		}
	};
	worker.promise.then(function() {
		if (task.destroyed) throw new Error("Loading aborted");
		if (worker.destroyed) throw new Error("Worker was destroyed");
		const workerIdPromise = worker.messageHandler.sendWithPromise("GetDocRequest", docParams, data ? [data.buffer] : null);
		let networkStream;
		if (rangeTransport) networkStream = new PDFDataTransportStream(rangeTransport, {
			disableRange,
			disableStream
		});
		else if (!data) {
			if (!url) throw new Error("getDocument - no `url` parameter provided.");
			let NetworkStream;
			if (isNodeJS) {
				if (isValidFetchUrl(url)) {
					if (typeof fetch === "undefined" || typeof Response === "undefined" || !("body" in Response.prototype)) throw new Error("getDocument - the Fetch API was disabled in Node.js, see `--no-experimental-fetch`.");
					NetworkStream = PDFFetchStream;
				} else NetworkStream = PDFNodeStream;
			} else NetworkStream = isValidFetchUrl(url) ? PDFFetchStream : PDFNetworkStream;
			networkStream = new NetworkStream({
				url,
				length,
				httpHeaders,
				withCredentials,
				rangeChunkSize,
				disableRange,
				disableStream
			});
		}
		return workerIdPromise.then((workerId) => {
			if (task.destroyed) throw new Error("Loading aborted");
			if (worker.destroyed) throw new Error("Worker was destroyed");
			const messageHandler = new MessageHandler(docId, workerId, worker.port);
			const transport = new WorkerTransport(messageHandler, task, networkStream, transportParams, transportFactory);
			task._transport = transport;
			messageHandler.send("Ready", null);
		});
	}).catch(task._capability.reject);
	return task;
}
function getUrlProp(val) {
	if (val instanceof URL) return val.href;
	try {
		return new URL(val, window.location).href;
	} catch {
		if (isNodeJS && typeof val === "string") return val;
	}
	throw new Error("Invalid PDF url data: either string or URL-object is expected in the url property.");
}
function getDataProp(val) {
	if (isNodeJS && typeof Buffer !== "undefined" && val instanceof Buffer) throw new Error("Please provide binary data as `Uint8Array`, rather than `Buffer`.");
	if (val instanceof Uint8Array && val.byteLength === val.buffer.byteLength) return val;
	if (typeof val === "string") return stringToBytes(val);
	if (val instanceof ArrayBuffer || ArrayBuffer.isView(val) || typeof val === "object" && !isNaN(val?.length)) return new Uint8Array(val);
	throw new Error("Invalid PDF binary data: either TypedArray, string, or array-like object is expected in the data property.");
}
function isRefProxy(ref) {
	return typeof ref === "object" && Number.isInteger(ref?.num) && ref.num >= 0 && Number.isInteger(ref?.gen) && ref.gen >= 0;
}
var PDFDocumentLoadingTask = class PDFDocumentLoadingTask {
	static #docId = 0;
	constructor() {
		this._capability = Promise.withResolvers();
		this._transport = null;
		this._worker = null;
		this.docId = `d${PDFDocumentLoadingTask.#docId++}`;
		this.destroyed = false;
		this.onPassword = null;
		this.onProgress = null;
	}
	get promise() {
		return this._capability.promise;
	}
	async destroy() {
		this.destroyed = true;
		try {
			if (this._worker?.port) this._worker._pendingDestroy = true;
			await this._transport?.destroy();
		} catch (ex) {
			if (this._worker?.port) delete this._worker._pendingDestroy;
			throw ex;
		}
		this._transport = null;
		this._worker?.destroy();
		this._worker = null;
	}
};
var PDFDataRangeTransport$1 = class {
	constructor(length, initialData, progressiveDone = false, contentDispositionFilename = null) {
		this.length = length;
		this.initialData = initialData;
		this.progressiveDone = progressiveDone;
		this.contentDispositionFilename = contentDispositionFilename;
		this._rangeListeners = [];
		this._progressListeners = [];
		this._progressiveReadListeners = [];
		this._progressiveDoneListeners = [];
		this._readyCapability = Promise.withResolvers();
	}
	addRangeListener(listener) {
		this._rangeListeners.push(listener);
	}
	addProgressListener(listener) {
		this._progressListeners.push(listener);
	}
	addProgressiveReadListener(listener) {
		this._progressiveReadListeners.push(listener);
	}
	addProgressiveDoneListener(listener) {
		this._progressiveDoneListeners.push(listener);
	}
	onDataRange(begin, chunk) {
		for (const listener of this._rangeListeners) listener(begin, chunk);
	}
	onDataProgress(loaded, total) {
		this._readyCapability.promise.then(() => {
			for (const listener of this._progressListeners) listener(loaded, total);
		});
	}
	onDataProgressiveRead(chunk) {
		this._readyCapability.promise.then(() => {
			for (const listener of this._progressiveReadListeners) listener(chunk);
		});
	}
	onDataProgressiveDone() {
		this._readyCapability.promise.then(() => {
			for (const listener of this._progressiveDoneListeners) listener();
		});
	}
	transportReady() {
		this._readyCapability.resolve();
	}
	requestDataRange(begin, end) {
		unreachable("Abstract method PDFDataRangeTransport.requestDataRange");
	}
	abort() {}
};
var PDFDocumentProxy = class {
	constructor(pdfInfo, transport) {
		this._pdfInfo = pdfInfo;
		this._transport = transport;
	}
	get annotationStorage() {
		return this._transport.annotationStorage;
	}
	get canvasFactory() {
		return this._transport.canvasFactory;
	}
	get filterFactory() {
		return this._transport.filterFactory;
	}
	get numPages() {
		return this._pdfInfo.numPages;
	}
	get fingerprints() {
		return this._pdfInfo.fingerprints;
	}
	get isPureXfa() {
		return shadow$1(this, "isPureXfa", !!this._transport._htmlForXfa);
	}
	get allXfaHtml() {
		return this._transport._htmlForXfa;
	}
	getPage(pageNumber) {
		return this._transport.getPage(pageNumber);
	}
	getPageIndex(ref) {
		return this._transport.getPageIndex(ref);
	}
	getDestinations() {
		return this._transport.getDestinations();
	}
	getDestination(id) {
		return this._transport.getDestination(id);
	}
	getPageLabels() {
		return this._transport.getPageLabels();
	}
	getPageLayout() {
		return this._transport.getPageLayout();
	}
	getPageMode() {
		return this._transport.getPageMode();
	}
	getViewerPreferences() {
		return this._transport.getViewerPreferences();
	}
	getOpenAction() {
		return this._transport.getOpenAction();
	}
	getAttachments() {
		return this._transport.getAttachments();
	}
	getJSActions() {
		return this._transport.getDocJSActions();
	}
	getOutline() {
		return this._transport.getOutline();
	}
	getOptionalContentConfig({ intent = "display" } = {}) {
		const { renderingIntent } = this._transport.getRenderingIntent(intent);
		return this._transport.getOptionalContentConfig(renderingIntent);
	}
	getPermissions() {
		return this._transport.getPermissions();
	}
	getMetadata() {
		return this._transport.getMetadata();
	}
	getMarkInfo() {
		return this._transport.getMarkInfo();
	}
	getData() {
		return this._transport.getData();
	}
	saveDocument() {
		return this._transport.saveDocument();
	}
	getDownloadInfo() {
		return this._transport.downloadInfoCapability.promise;
	}
	cleanup(keepLoadedFonts = false) {
		return this._transport.startCleanup(keepLoadedFonts || this.isPureXfa);
	}
	destroy() {
		return this.loadingTask.destroy();
	}
	cachedPageNumber(ref) {
		return this._transport.cachedPageNumber(ref);
	}
	get loadingParams() {
		return this._transport.loadingParams;
	}
	get loadingTask() {
		return this._transport.loadingTask;
	}
	getFieldObjects() {
		return this._transport.getFieldObjects();
	}
	hasJSActions() {
		return this._transport.hasJSActions();
	}
	getCalculationOrderIds() {
		return this._transport.getCalculationOrderIds();
	}
};
var PDFPageProxy = class {
	#delayedCleanupTimeout = null;
	#pendingCleanup = false;
	constructor(pageIndex, pageInfo, transport, pdfBug = false) {
		this._pageIndex = pageIndex;
		this._pageInfo = pageInfo;
		this._transport = transport;
		this._stats = pdfBug ? new StatTimer() : null;
		this._pdfBug = pdfBug;
		this.commonObjs = transport.commonObjs;
		this.objs = new PDFObjects();
		this._maybeCleanupAfterRender = false;
		this._intentStates = /* @__PURE__ */ new Map();
		this.destroyed = false;
	}
	get pageNumber() {
		return this._pageIndex + 1;
	}
	get rotate() {
		return this._pageInfo.rotate;
	}
	get ref() {
		return this._pageInfo.ref;
	}
	get userUnit() {
		return this._pageInfo.userUnit;
	}
	get view() {
		return this._pageInfo.view;
	}
	getViewport({ scale, rotation = this.rotate, offsetX = 0, offsetY = 0, dontFlip = false } = {}) {
		return new PageViewport({
			viewBox: this.view,
			userUnit: this.userUnit,
			scale,
			rotation,
			offsetX,
			offsetY,
			dontFlip
		});
	}
	getAnnotations({ intent = "display" } = {}) {
		const { renderingIntent } = this._transport.getRenderingIntent(intent);
		return this._transport.getAnnotations(this._pageIndex, renderingIntent);
	}
	getJSActions() {
		return this._transport.getPageJSActions(this._pageIndex);
	}
	get filterFactory() {
		return this._transport.filterFactory;
	}
	get isPureXfa() {
		return shadow$1(this, "isPureXfa", !!this._transport._htmlForXfa);
	}
	async getXfa() {
		return this._transport._htmlForXfa?.children[this._pageIndex] || null;
	}
	render({ canvasContext, viewport, intent = "display", annotationMode = AnnotationMode$1.ENABLE, transform = null, background = null, optionalContentConfigPromise = null, annotationCanvasMap = null, pageColors = null, printAnnotationStorage = null, isEditing = false }) {
		this._stats?.time("Overall");
		const intentArgs = this._transport.getRenderingIntent(intent, annotationMode, printAnnotationStorage, isEditing);
		const { renderingIntent, cacheKey } = intentArgs;
		this.#pendingCleanup = false;
		this.#abortDelayedCleanup();
		optionalContentConfigPromise ||= this._transport.getOptionalContentConfig(renderingIntent);
		let intentState = this._intentStates.get(cacheKey);
		if (!intentState) {
			intentState = Object.create(null);
			this._intentStates.set(cacheKey, intentState);
		}
		if (intentState.streamReaderCancelTimeout) {
			clearTimeout(intentState.streamReaderCancelTimeout);
			intentState.streamReaderCancelTimeout = null;
		}
		const intentPrint = !!(renderingIntent & RenderingIntentFlag.PRINT);
		if (!intentState.displayReadyCapability) {
			intentState.displayReadyCapability = Promise.withResolvers();
			intentState.operatorList = {
				fnArray: [],
				argsArray: [],
				lastChunk: false,
				separateAnnots: null
			};
			this._stats?.time("Page Request");
			this._pumpOperatorList(intentArgs);
		}
		const complete = (error) => {
			intentState.renderTasks.delete(internalRenderTask);
			if (this._maybeCleanupAfterRender || intentPrint) this.#pendingCleanup = true;
			this.#tryCleanup(!intentPrint);
			if (error) {
				internalRenderTask.capability.reject(error);
				this._abortOperatorList({
					intentState,
					reason: error instanceof Error ? error : new Error(error)
				});
			} else internalRenderTask.capability.resolve();
			if (this._stats) {
				this._stats.timeEnd("Rendering");
				this._stats.timeEnd("Overall");
				if (globalThis.Stats?.enabled) globalThis.Stats.add(this.pageNumber, this._stats);
			}
		};
		const internalRenderTask = new InternalRenderTask({
			callback: complete,
			params: {
				canvasContext,
				viewport,
				transform,
				background
			},
			objs: this.objs,
			commonObjs: this.commonObjs,
			annotationCanvasMap,
			operatorList: intentState.operatorList,
			pageIndex: this._pageIndex,
			canvasFactory: this._transport.canvasFactory,
			filterFactory: this._transport.filterFactory,
			useRequestAnimationFrame: !intentPrint,
			pdfBug: this._pdfBug,
			pageColors
		});
		(intentState.renderTasks ||= /* @__PURE__ */ new Set()).add(internalRenderTask);
		const renderTask = internalRenderTask.task;
		Promise.all([intentState.displayReadyCapability.promise, optionalContentConfigPromise]).then(([transparency, optionalContentConfig]) => {
			if (this.destroyed) {
				complete();
				return;
			}
			this._stats?.time("Rendering");
			if (!(optionalContentConfig.renderingIntent & renderingIntent)) throw new Error("Must use the same `intent`-argument when calling the `PDFPageProxy.render` and `PDFDocumentProxy.getOptionalContentConfig` methods.");
			internalRenderTask.initializeGraphics({
				transparency,
				optionalContentConfig
			});
			internalRenderTask.operatorListChanged();
		}).catch(complete);
		return renderTask;
	}
	getOperatorList({ intent = "display", annotationMode = AnnotationMode$1.ENABLE, printAnnotationStorage = null, isEditing = false } = {}) {
		function operatorListChanged() {
			if (intentState.operatorList.lastChunk) {
				intentState.opListReadCapability.resolve(intentState.operatorList);
				intentState.renderTasks.delete(opListTask);
			}
		}
		const intentArgs = this._transport.getRenderingIntent(intent, annotationMode, printAnnotationStorage, isEditing, true);
		let intentState = this._intentStates.get(intentArgs.cacheKey);
		if (!intentState) {
			intentState = Object.create(null);
			this._intentStates.set(intentArgs.cacheKey, intentState);
		}
		let opListTask;
		if (!intentState.opListReadCapability) {
			opListTask = Object.create(null);
			opListTask.operatorListChanged = operatorListChanged;
			intentState.opListReadCapability = Promise.withResolvers();
			(intentState.renderTasks ||= /* @__PURE__ */ new Set()).add(opListTask);
			intentState.operatorList = {
				fnArray: [],
				argsArray: [],
				lastChunk: false,
				separateAnnots: null
			};
			this._stats?.time("Page Request");
			this._pumpOperatorList(intentArgs);
		}
		return intentState.opListReadCapability.promise;
	}
	streamTextContent({ includeMarkedContent = false, disableNormalization = false } = {}) {
		return this._transport.messageHandler.sendWithStream("GetTextContent", {
			pageIndex: this._pageIndex,
			includeMarkedContent: includeMarkedContent === true,
			disableNormalization: disableNormalization === true
		}, {
			highWaterMark: 100,
			size(textContent) {
				return textContent.items.length;
			}
		});
	}
	getTextContent(params = {}) {
		if (this._transport._htmlForXfa) return this.getXfa().then((xfa) => XfaText.textContent(xfa));
		const readableStream = this.streamTextContent(params);
		return new Promise(function(resolve, reject) {
			function pump() {
				reader.read().then(function({ value, done }) {
					if (done) {
						resolve(textContent);
						return;
					}
					textContent.lang ??= value.lang;
					Object.assign(textContent.styles, value.styles);
					textContent.items.push(...value.items);
					pump();
				}, reject);
			}
			const reader = readableStream.getReader();
			const textContent = {
				items: [],
				styles: Object.create(null),
				lang: null
			};
			pump();
		});
	}
	getStructTree() {
		return this._transport.getStructTree(this._pageIndex);
	}
	_destroy() {
		this.destroyed = true;
		const waitOn = [];
		for (const intentState of this._intentStates.values()) {
			this._abortOperatorList({
				intentState,
				reason: /* @__PURE__ */ new Error("Page was destroyed."),
				force: true
			});
			if (intentState.opListReadCapability) continue;
			for (const internalRenderTask of intentState.renderTasks) {
				waitOn.push(internalRenderTask.completed);
				internalRenderTask.cancel();
			}
		}
		this.objs.clear();
		this.#pendingCleanup = false;
		this.#abortDelayedCleanup();
		return Promise.all(waitOn);
	}
	cleanup(resetStats = false) {
		this.#pendingCleanup = true;
		const success = this.#tryCleanup(false);
		if (resetStats && success) this._stats &&= new StatTimer();
		return success;
	}
	#tryCleanup(delayed = false) {
		this.#abortDelayedCleanup();
		if (!this.#pendingCleanup || this.destroyed) return false;
		if (delayed) {
			this.#delayedCleanupTimeout = setTimeout(() => {
				this.#delayedCleanupTimeout = null;
				this.#tryCleanup(false);
			}, DELAYED_CLEANUP_TIMEOUT);
			return false;
		}
		for (const { renderTasks, operatorList } of this._intentStates.values()) if (renderTasks.size > 0 || !operatorList.lastChunk) return false;
		this._intentStates.clear();
		this.objs.clear();
		this.#pendingCleanup = false;
		return true;
	}
	#abortDelayedCleanup() {
		if (this.#delayedCleanupTimeout) {
			clearTimeout(this.#delayedCleanupTimeout);
			this.#delayedCleanupTimeout = null;
		}
	}
	_startRenderPage(transparency, cacheKey) {
		const intentState = this._intentStates.get(cacheKey);
		if (!intentState) return;
		this._stats?.timeEnd("Page Request");
		intentState.displayReadyCapability?.resolve(transparency);
	}
	_renderPageChunk(operatorListChunk, intentState) {
		for (let i = 0, ii = operatorListChunk.length; i < ii; i++) {
			intentState.operatorList.fnArray.push(operatorListChunk.fnArray[i]);
			intentState.operatorList.argsArray.push(operatorListChunk.argsArray[i]);
		}
		intentState.operatorList.lastChunk = operatorListChunk.lastChunk;
		intentState.operatorList.separateAnnots = operatorListChunk.separateAnnots;
		for (const internalRenderTask of intentState.renderTasks) internalRenderTask.operatorListChanged();
		if (operatorListChunk.lastChunk) this.#tryCleanup(true);
	}
	_pumpOperatorList({ renderingIntent, cacheKey, annotationStorageSerializable, modifiedIds }) {
		const { map, transfer } = annotationStorageSerializable;
		const reader = this._transport.messageHandler.sendWithStream("GetOperatorList", {
			pageIndex: this._pageIndex,
			intent: renderingIntent,
			cacheKey,
			annotationStorage: map,
			modifiedIds
		}, transfer).getReader();
		const intentState = this._intentStates.get(cacheKey);
		intentState.streamReader = reader;
		const pump = () => {
			reader.read().then(({ value, done }) => {
				if (done) {
					intentState.streamReader = null;
					return;
				}
				if (this._transport.destroyed) return;
				this._renderPageChunk(value, intentState);
				pump();
			}, (reason) => {
				intentState.streamReader = null;
				if (this._transport.destroyed) return;
				if (intentState.operatorList) {
					intentState.operatorList.lastChunk = true;
					for (const internalRenderTask of intentState.renderTasks) internalRenderTask.operatorListChanged();
					this.#tryCleanup(true);
				}
				if (intentState.displayReadyCapability) intentState.displayReadyCapability.reject(reason);
				else if (intentState.opListReadCapability) intentState.opListReadCapability.reject(reason);
				else throw reason;
			});
		};
		pump();
	}
	_abortOperatorList({ intentState, reason, force = false }) {
		if (!intentState.streamReader) return;
		if (intentState.streamReaderCancelTimeout) {
			clearTimeout(intentState.streamReaderCancelTimeout);
			intentState.streamReaderCancelTimeout = null;
		}
		if (!force) {
			if (intentState.renderTasks.size > 0) return;
			if (reason instanceof RenderingCancelledException$1) {
				let delay = RENDERING_CANCELLED_TIMEOUT;
				if (reason.extraDelay > 0 && reason.extraDelay < 1e3) delay += reason.extraDelay;
				intentState.streamReaderCancelTimeout = setTimeout(() => {
					intentState.streamReaderCancelTimeout = null;
					this._abortOperatorList({
						intentState,
						reason,
						force: true
					});
				}, delay);
				return;
			}
		}
		intentState.streamReader.cancel(new AbortException$1(reason.message)).catch(() => {});
		intentState.streamReader = null;
		if (this._transport.destroyed) return;
		for (const [curCacheKey, curIntentState] of this._intentStates) if (curIntentState === intentState) {
			this._intentStates.delete(curCacheKey);
			break;
		}
		this.cleanup();
	}
	get stats() {
		return this._stats;
	}
};
var LoopbackPort = class {
	#listeners = /* @__PURE__ */ new Map();
	#deferred = Promise.resolve();
	postMessage(obj, transfer) {
		const event = { data: structuredClone(obj, transfer ? { transfer } : null) };
		this.#deferred.then(() => {
			for (const [listener] of this.#listeners) listener.call(this, event);
		});
	}
	addEventListener(name, listener, options = null) {
		let rmAbort = null;
		if (options?.signal instanceof AbortSignal) {
			const { signal } = options;
			if (signal.aborted) {
				warn("LoopbackPort - cannot use an `aborted` signal.");
				return;
			}
			const onAbort = () => this.removeEventListener(name, listener);
			rmAbort = () => signal.removeEventListener("abort", onAbort);
			signal.addEventListener("abort", onAbort);
		}
		this.#listeners.set(listener, rmAbort);
	}
	removeEventListener(name, listener) {
		this.#listeners.get(listener)?.();
		this.#listeners.delete(listener);
	}
	terminate() {
		for (const [, rmAbort] of this.#listeners) rmAbort?.();
		this.#listeners.clear();
	}
};
var PDFWorker$1 = class PDFWorker$1 {
	static #fakeWorkerId = 0;
	static #isWorkerDisabled = false;
	static #workerPorts;
	static {
		if (isNodeJS) {
			this.#isWorkerDisabled = true;
			GlobalWorkerOptions$2.workerSrc ||= "./pdf.worker.mjs";
		}
		this._isSameOrigin = (baseUrl, otherUrl) => {
			let base;
			try {
				base = new URL(baseUrl);
				if (!base.origin || base.origin === "null") return false;
			} catch {
				return false;
			}
			const other = new URL(otherUrl, base);
			return base.origin === other.origin;
		};
		this._createCDNWrapper = (url) => {
			throw new Error("Cross-origin PDF.js workers are not supported by the packaged plugin.");
		};
	}
	constructor({ name = null, port = null, verbosity = getVerbosityLevel() } = {}) {
		this.name = name;
		this.destroyed = false;
		this.verbosity = verbosity;
		this._readyCapability = Promise.withResolvers();
		this._port = null;
		this._webWorker = null;
		this._messageHandler = null;
		if (port) {
			if (PDFWorker$1.#workerPorts?.has(port)) throw new Error("Cannot use more than one PDFWorker per port.");
			(PDFWorker$1.#workerPorts ||= /* @__PURE__ */ new WeakMap()).set(port, this);
			this._initializeFromPort(port);
			return;
		}
		this._initialize();
	}
	get promise() {
		return this._readyCapability.promise;
	}
	#resolve() {
		this._readyCapability.resolve();
		this._messageHandler.send("configure", { verbosity: this.verbosity });
	}
	get port() {
		return this._port;
	}
	get messageHandler() {
		return this._messageHandler;
	}
	_initializeFromPort(port) {
		this._port = port;
		this._messageHandler = new MessageHandler("main", "worker", port);
		this._messageHandler.on("ready", function() {});
		this.#resolve();
	}
	_initialize() {
		if (PDFWorker$1.#isWorkerDisabled || PDFWorker$1.#mainThreadWorkerMessageHandler) {
			this._setupFakeWorker();
			return;
		}
		let { workerSrc } = PDFWorker$1;
		try {
			if (!PDFWorker$1._isSameOrigin(window.location.href, workerSrc)) workerSrc = PDFWorker$1._createCDNWrapper(new URL(workerSrc, window.location).href);
			const worker = new Worker(workerSrc, { type: "module" });
			const messageHandler = new MessageHandler("main", "worker", worker);
			const terminateEarly = () => {
				ac.abort();
				messageHandler.destroy();
				worker.terminate();
				if (this.destroyed) this._readyCapability.reject(/* @__PURE__ */ new Error("Worker was destroyed"));
				else this._setupFakeWorker();
			};
			const ac = new AbortController();
			worker.addEventListener("error", () => {
				if (!this._webWorker) terminateEarly();
			}, { signal: ac.signal });
			messageHandler.on("test", (data) => {
				ac.abort();
				if (this.destroyed || !data) {
					terminateEarly();
					return;
				}
				this._messageHandler = messageHandler;
				this._port = worker;
				this._webWorker = worker;
				this.#resolve();
			});
			messageHandler.on("ready", (data) => {
				ac.abort();
				if (this.destroyed) {
					terminateEarly();
					return;
				}
				try {
					sendTest();
				} catch {
					this._setupFakeWorker();
				}
			});
			const sendTest = () => {
				const testObj = /* @__PURE__ */ new Uint8Array();
				messageHandler.send("test", testObj, [testObj.buffer]);
			};
			sendTest();
			return;
		} catch {
			info("The worker has been disabled.");
		}
		this._setupFakeWorker();
	}
	_setupFakeWorker() {
		if (!PDFWorker$1.#isWorkerDisabled) {
			warn("Setting up fake worker.");
			PDFWorker$1.#isWorkerDisabled = true;
		}
		PDFWorker$1._setupFakeWorkerGlobal.then((WorkerMessageHandler) => {
			if (this.destroyed) {
				this._readyCapability.reject(/* @__PURE__ */ new Error("Worker was destroyed"));
				return;
			}
			const port = new LoopbackPort();
			this._port = port;
			const id = `fake${PDFWorker$1.#fakeWorkerId++}`;
			const workerHandler = new MessageHandler(id + "_worker", id, port);
			WorkerMessageHandler.setup(workerHandler, port);
			this._messageHandler = new MessageHandler(id, id + "_worker", port);
			this.#resolve();
		}).catch((reason) => {
			this._readyCapability.reject(/* @__PURE__ */ new Error(`Setting up fake worker failed: "${reason.message}".`));
		});
	}
	destroy() {
		this.destroyed = true;
		this._webWorker?.terminate();
		this._webWorker = null;
		PDFWorker$1.#workerPorts?.delete(this._port);
		this._port = null;
		this._messageHandler?.destroy();
		this._messageHandler = null;
	}
	static fromPort(params) {
		if (!params?.port) throw new Error("PDFWorker.fromPort - invalid method signature.");
		const cachedPort = this.#workerPorts?.get(params.port);
		if (cachedPort) {
			if (cachedPort._pendingDestroy) throw new Error("PDFWorker.fromPort - the worker is being destroyed.\nPlease remember to await `PDFDocumentLoadingTask.destroy()`-calls.");
			return cachedPort;
		}
		return new PDFWorker$1(params);
	}
	static get workerSrc() {
		if (GlobalWorkerOptions$2.workerSrc) return GlobalWorkerOptions$2.workerSrc;
		throw new Error("No \"GlobalWorkerOptions.workerSrc\" specified.");
	}
	static get #mainThreadWorkerMessageHandler() {
		try {
			return globalThis.pdfjsWorker?.WorkerMessageHandler || null;
		} catch {
			return null;
		}
	}
	static get _setupFakeWorkerGlobal() {
		const loader = async () => {
			if (this.#mainThreadWorkerMessageHandler) return this.#mainThreadWorkerMessageHandler;
			throw new Error("PDF.js worker is unavailable and dynamic module fallback is disabled.");
		};
		return shadow$1(this, "_setupFakeWorkerGlobal", loader());
	}
};
var WorkerTransport = class {
	#methodPromises = /* @__PURE__ */ new Map();
	#pageCache = /* @__PURE__ */ new Map();
	#pagePromises = /* @__PURE__ */ new Map();
	#pageRefCache = /* @__PURE__ */ new Map();
	#passwordCapability = null;
	constructor(messageHandler, loadingTask, networkStream, params, factory) {
		this.messageHandler = messageHandler;
		this.loadingTask = loadingTask;
		this.commonObjs = new PDFObjects();
		this.fontLoader = new FontLoader({
			ownerDocument: params.ownerDocument,
			styleElement: params.styleElement
		});
		this.loadingParams = params.loadingParams;
		this._params = params;
		this.canvasFactory = factory.canvasFactory;
		this.filterFactory = factory.filterFactory;
		this.cMapReaderFactory = factory.cMapReaderFactory;
		this.standardFontDataFactory = factory.standardFontDataFactory;
		this.destroyed = false;
		this.destroyCapability = null;
		this._networkStream = networkStream;
		this._fullReader = null;
		this._lastProgress = null;
		this.downloadInfoCapability = Promise.withResolvers();
		this.setupMessageHandler();
	}
	#cacheSimpleMethod(name, data = null) {
		const cachedPromise = this.#methodPromises.get(name);
		if (cachedPromise) return cachedPromise;
		const promise = this.messageHandler.sendWithPromise(name, data);
		this.#methodPromises.set(name, promise);
		return promise;
	}
	get annotationStorage() {
		return shadow$1(this, "annotationStorage", new AnnotationStorage());
	}
	getRenderingIntent(intent, annotationMode = AnnotationMode$1.ENABLE, printAnnotationStorage = null, isEditing = false, isOpList = false) {
		let renderingIntent = RenderingIntentFlag.DISPLAY;
		let annotationStorageSerializable = SerializableEmpty;
		switch (intent) {
			case "any":
				renderingIntent = RenderingIntentFlag.ANY;
				break;
			case "display": break;
			case "print":
				renderingIntent = RenderingIntentFlag.PRINT;
				break;
			default: warn(`getRenderingIntent - invalid intent: ${intent}`);
		}
		const annotationStorage = renderingIntent & RenderingIntentFlag.PRINT && printAnnotationStorage instanceof PrintAnnotationStorage ? printAnnotationStorage : this.annotationStorage;
		switch (annotationMode) {
			case AnnotationMode$1.DISABLE:
				renderingIntent += RenderingIntentFlag.ANNOTATIONS_DISABLE;
				break;
			case AnnotationMode$1.ENABLE: break;
			case AnnotationMode$1.ENABLE_FORMS:
				renderingIntent += RenderingIntentFlag.ANNOTATIONS_FORMS;
				break;
			case AnnotationMode$1.ENABLE_STORAGE:
				renderingIntent += RenderingIntentFlag.ANNOTATIONS_STORAGE;
				annotationStorageSerializable = annotationStorage.serializable;
				break;
			default: warn(`getRenderingIntent - invalid annotationMode: ${annotationMode}`);
		}
		if (isEditing) renderingIntent += RenderingIntentFlag.IS_EDITING;
		if (isOpList) renderingIntent += RenderingIntentFlag.OPLIST;
		const { ids: modifiedIds, hash: modifiedIdsHash } = annotationStorage.modifiedIds;
		const cacheKeyBuf = [
			renderingIntent,
			annotationStorageSerializable.hash,
			modifiedIdsHash
		];
		return {
			renderingIntent,
			cacheKey: cacheKeyBuf.join("_"),
			annotationStorageSerializable,
			modifiedIds
		};
	}
	destroy() {
		if (this.destroyCapability) return this.destroyCapability.promise;
		this.destroyed = true;
		this.destroyCapability = Promise.withResolvers();
		this.#passwordCapability?.reject(/* @__PURE__ */ new Error("Worker was destroyed during onPassword callback"));
		const waitOn = [];
		for (const page of this.#pageCache.values()) waitOn.push(page._destroy());
		this.#pageCache.clear();
		this.#pagePromises.clear();
		this.#pageRefCache.clear();
		if (this.hasOwnProperty("annotationStorage")) this.annotationStorage.resetModified();
		const terminated = this.messageHandler.sendWithPromise("Terminate", null);
		waitOn.push(terminated);
		Promise.all(waitOn).then(() => {
			this.commonObjs.clear();
			this.fontLoader.clear();
			this.#methodPromises.clear();
			this.filterFactory.destroy();
			TextLayer$1.cleanup();
			this._networkStream?.cancelAllRequests(new AbortException$1("Worker was terminated."));
			this.messageHandler?.destroy();
			this.messageHandler = null;
			this.destroyCapability.resolve();
		}, this.destroyCapability.reject);
		return this.destroyCapability.promise;
	}
	setupMessageHandler() {
		const { messageHandler, loadingTask } = this;
		messageHandler.on("GetReader", (data, sink) => {
			assert(this._networkStream, "GetReader - no `IPDFStream` instance available.");
			this._fullReader = this._networkStream.getFullReader();
			this._fullReader.onProgress = (evt) => {
				this._lastProgress = {
					loaded: evt.loaded,
					total: evt.total
				};
			};
			sink.onPull = () => {
				this._fullReader.read().then(function({ value, done }) {
					if (done) {
						sink.close();
						return;
					}
					assert(value instanceof ArrayBuffer, "GetReader - expected an ArrayBuffer.");
					sink.enqueue(new Uint8Array(value), 1, [value]);
				}).catch((reason) => {
					sink.error(reason);
				});
			};
			sink.onCancel = (reason) => {
				this._fullReader.cancel(reason);
				sink.ready.catch((readyReason) => {
					if (this.destroyed) return;
					throw readyReason;
				});
			};
		});
		messageHandler.on("ReaderHeadersReady", async (data) => {
			await this._fullReader.headersReady;
			const { isStreamingSupported, isRangeSupported, contentLength } = this._fullReader;
			if (!isStreamingSupported || !isRangeSupported) {
				if (this._lastProgress) loadingTask.onProgress?.(this._lastProgress);
				this._fullReader.onProgress = (evt) => {
					loadingTask.onProgress?.({
						loaded: evt.loaded,
						total: evt.total
					});
				};
			}
			return {
				isStreamingSupported,
				isRangeSupported,
				contentLength
			};
		});
		messageHandler.on("GetRangeReader", (data, sink) => {
			assert(this._networkStream, "GetRangeReader - no `IPDFStream` instance available.");
			const rangeReader = this._networkStream.getRangeReader(data.begin, data.end);
			if (!rangeReader) {
				sink.close();
				return;
			}
			sink.onPull = () => {
				rangeReader.read().then(function({ value, done }) {
					if (done) {
						sink.close();
						return;
					}
					assert(value instanceof ArrayBuffer, "GetRangeReader - expected an ArrayBuffer.");
					sink.enqueue(new Uint8Array(value), 1, [value]);
				}).catch((reason) => {
					sink.error(reason);
				});
			};
			sink.onCancel = (reason) => {
				rangeReader.cancel(reason);
				sink.ready.catch((readyReason) => {
					if (this.destroyed) return;
					throw readyReason;
				});
			};
		});
		messageHandler.on("GetDoc", ({ pdfInfo }) => {
			this._numPages = pdfInfo.numPages;
			this._htmlForXfa = pdfInfo.htmlForXfa;
			delete pdfInfo.htmlForXfa;
			loadingTask._capability.resolve(new PDFDocumentProxy(pdfInfo, this));
		});
		messageHandler.on("DocException", (ex) => {
			loadingTask._capability.reject(wrapReason(ex));
		});
		messageHandler.on("PasswordRequest", (ex) => {
			this.#passwordCapability = Promise.withResolvers();
			try {
				if (!loadingTask.onPassword) throw wrapReason(ex);
				const updatePassword = (password) => {
					if (password instanceof Error) this.#passwordCapability.reject(password);
					else this.#passwordCapability.resolve({ password });
				};
				loadingTask.onPassword(updatePassword, ex.code);
			} catch (err) {
				this.#passwordCapability.reject(err);
			}
			return this.#passwordCapability.promise;
		});
		messageHandler.on("DataLoaded", (data) => {
			loadingTask.onProgress?.({
				loaded: data.length,
				total: data.length
			});
			this.downloadInfoCapability.resolve(data);
		});
		messageHandler.on("StartRenderPage", (data) => {
			if (this.destroyed) return;
			this.#pageCache.get(data.pageIndex)._startRenderPage(data.transparency, data.cacheKey);
		});
		messageHandler.on("commonobj", ([id, type, exportedData]) => {
			if (this.destroyed) return null;
			if (this.commonObjs.has(id)) return null;
			switch (type) {
				case "Font":
					const { disableFontFace, fontExtraProperties, pdfBug } = this._params;
					if ("error" in exportedData) {
						const exportedError = exportedData.error;
						warn(`Error during font loading: ${exportedError}`);
						this.commonObjs.resolve(id, exportedError);
						break;
					}
					const font = new FontFaceObject(exportedData, {
						disableFontFace,
						fontExtraProperties,
						inspectFont: pdfBug && globalThis.FontInspector?.enabled ? (font, url) => globalThis.FontInspector.fontAdded(font, url) : null
					});
					this.fontLoader.bind(font).catch(() => messageHandler.sendWithPromise("FontFallback", { id })).finally(() => {
						if (!fontExtraProperties && font.data) font.data = null;
						this.commonObjs.resolve(id, font);
					});
					break;
				case "CopyLocalImage":
					const { imageRef } = exportedData;
					assert(imageRef, "The imageRef must be defined.");
					for (const pageProxy of this.#pageCache.values()) for (const [, data] of pageProxy.objs) {
						if (data?.ref !== imageRef) continue;
						if (!data.dataLen) return null;
						this.commonObjs.resolve(id, structuredClone(data));
						return data.dataLen;
					}
					break;
				case "FontPath":
				case "Image":
				case "Pattern":
					this.commonObjs.resolve(id, exportedData);
					break;
				default: throw new Error(`Got unknown common object type ${type}`);
			}
			return null;
		});
		messageHandler.on("obj", ([id, pageIndex, type, imageData]) => {
			if (this.destroyed) return;
			const pageProxy = this.#pageCache.get(pageIndex);
			if (pageProxy.objs.has(id)) return;
			if (pageProxy._intentStates.size === 0) {
				imageData?.bitmap?.close();
				return;
			}
			switch (type) {
				case "Image":
					pageProxy.objs.resolve(id, imageData);
					if (imageData?.dataLen > MAX_IMAGE_SIZE_TO_CACHE) pageProxy._maybeCleanupAfterRender = true;
					break;
				case "Pattern":
					pageProxy.objs.resolve(id, imageData);
					break;
				default: throw new Error(`Got unknown object type ${type}`);
			}
		});
		messageHandler.on("DocProgress", (data) => {
			if (this.destroyed) return;
			loadingTask.onProgress?.({
				loaded: data.loaded,
				total: data.total
			});
		});
		messageHandler.on("FetchBuiltInCMap", async (data) => {
			if (this.destroyed) throw new Error("Worker was destroyed.");
			if (!this.cMapReaderFactory) throw new Error("CMapReaderFactory not initialized, see the `useWorkerFetch` parameter.");
			return this.cMapReaderFactory.fetch(data);
		});
		messageHandler.on("FetchStandardFontData", async (data) => {
			if (this.destroyed) throw new Error("Worker was destroyed.");
			if (!this.standardFontDataFactory) throw new Error("StandardFontDataFactory not initialized, see the `useWorkerFetch` parameter.");
			return this.standardFontDataFactory.fetch(data);
		});
	}
	getData() {
		return this.messageHandler.sendWithPromise("GetData", null);
	}
	saveDocument() {
		if (this.annotationStorage.size <= 0) warn("saveDocument called while `annotationStorage` is empty, please use the getData-method instead.");
		const { map, transfer } = this.annotationStorage.serializable;
		return this.messageHandler.sendWithPromise("SaveDocument", {
			isPureXfa: !!this._htmlForXfa,
			numPages: this._numPages,
			annotationStorage: map,
			filename: this._fullReader?.filename ?? null
		}, transfer).finally(() => {
			this.annotationStorage.resetModified();
		});
	}
	getPage(pageNumber) {
		if (!Number.isInteger(pageNumber) || pageNumber <= 0 || pageNumber > this._numPages) return Promise.reject(/* @__PURE__ */ new Error("Invalid page request."));
		const pageIndex = pageNumber - 1, cachedPromise = this.#pagePromises.get(pageIndex);
		if (cachedPromise) return cachedPromise;
		const promise = this.messageHandler.sendWithPromise("GetPage", { pageIndex }).then((pageInfo) => {
			if (this.destroyed) throw new Error("Transport destroyed");
			if (pageInfo.refStr) this.#pageRefCache.set(pageInfo.refStr, pageNumber);
			const page = new PDFPageProxy(pageIndex, pageInfo, this, this._params.pdfBug);
			this.#pageCache.set(pageIndex, page);
			return page;
		});
		this.#pagePromises.set(pageIndex, promise);
		return promise;
	}
	getPageIndex(ref) {
		if (!isRefProxy(ref)) return Promise.reject(/* @__PURE__ */ new Error("Invalid pageIndex request."));
		return this.messageHandler.sendWithPromise("GetPageIndex", {
			num: ref.num,
			gen: ref.gen
		});
	}
	getAnnotations(pageIndex, intent) {
		return this.messageHandler.sendWithPromise("GetAnnotations", {
			pageIndex,
			intent
		});
	}
	getFieldObjects() {
		return this.#cacheSimpleMethod("GetFieldObjects");
	}
	hasJSActions() {
		return this.#cacheSimpleMethod("HasJSActions");
	}
	getCalculationOrderIds() {
		return this.messageHandler.sendWithPromise("GetCalculationOrderIds", null);
	}
	getDestinations() {
		return this.messageHandler.sendWithPromise("GetDestinations", null);
	}
	getDestination(id) {
		if (typeof id !== "string") return Promise.reject(/* @__PURE__ */ new Error("Invalid destination request."));
		return this.messageHandler.sendWithPromise("GetDestination", { id });
	}
	getPageLabels() {
		return this.messageHandler.sendWithPromise("GetPageLabels", null);
	}
	getPageLayout() {
		return this.messageHandler.sendWithPromise("GetPageLayout", null);
	}
	getPageMode() {
		return this.messageHandler.sendWithPromise("GetPageMode", null);
	}
	getViewerPreferences() {
		return this.messageHandler.sendWithPromise("GetViewerPreferences", null);
	}
	getOpenAction() {
		return this.messageHandler.sendWithPromise("GetOpenAction", null);
	}
	getAttachments() {
		return this.messageHandler.sendWithPromise("GetAttachments", null);
	}
	getDocJSActions() {
		return this.#cacheSimpleMethod("GetDocJSActions");
	}
	getPageJSActions(pageIndex) {
		return this.messageHandler.sendWithPromise("GetPageJSActions", { pageIndex });
	}
	getStructTree(pageIndex) {
		return this.messageHandler.sendWithPromise("GetStructTree", { pageIndex });
	}
	getOutline() {
		return this.messageHandler.sendWithPromise("GetOutline", null);
	}
	getOptionalContentConfig(renderingIntent) {
		return this.#cacheSimpleMethod("GetOptionalContentConfig").then((data) => new OptionalContentConfig(data, renderingIntent));
	}
	getPermissions() {
		return this.messageHandler.sendWithPromise("GetPermissions", null);
	}
	getMetadata() {
		const name = "GetMetadata", cachedPromise = this.#methodPromises.get(name);
		if (cachedPromise) return cachedPromise;
		const promise = this.messageHandler.sendWithPromise(name, null).then((results) => ({
			info: results[0],
			metadata: results[1] ? new Metadata(results[1]) : null,
			contentDispositionFilename: this._fullReader?.filename ?? null,
			contentLength: this._fullReader?.contentLength ?? null
		}));
		this.#methodPromises.set(name, promise);
		return promise;
	}
	getMarkInfo() {
		return this.messageHandler.sendWithPromise("GetMarkInfo", null);
	}
	async startCleanup(keepLoadedFonts = false) {
		if (this.destroyed) return;
		await this.messageHandler.sendWithPromise("Cleanup", null);
		for (const page of this.#pageCache.values()) if (!page.cleanup()) throw new Error(`startCleanup: Page ${page.pageNumber} is currently rendering.`);
		this.commonObjs.clear();
		if (!keepLoadedFonts) this.fontLoader.clear();
		this.#methodPromises.clear();
		this.filterFactory.destroy(true);
		TextLayer$1.cleanup();
	}
	cachedPageNumber(ref) {
		if (!isRefProxy(ref)) return null;
		const refStr = ref.gen === 0 ? `${ref.num}R` : `${ref.num}R${ref.gen}`;
		return this.#pageRefCache.get(refStr) ?? null;
	}
};
var INITIAL_DATA = Symbol("INITIAL_DATA");
var PDFObjects = class {
	#objs = Object.create(null);
	#ensureObj(objId) {
		return this.#objs[objId] ||= {
			...Promise.withResolvers(),
			data: INITIAL_DATA
		};
	}
	get(objId, callback = null) {
		if (callback) {
			const obj = this.#ensureObj(objId);
			obj.promise.then(() => callback(obj.data));
			return null;
		}
		const obj = this.#objs[objId];
		if (!obj || obj.data === INITIAL_DATA) throw new Error(`Requesting object that isn't resolved yet ${objId}.`);
		return obj.data;
	}
	has(objId) {
		const obj = this.#objs[objId];
		return !!obj && obj.data !== INITIAL_DATA;
	}
	delete(objId) {
		const obj = this.#objs[objId];
		if (!obj || obj.data === INITIAL_DATA) return false;
		delete this.#objs[objId];
		return true;
	}
	resolve(objId, data = null) {
		const obj = this.#ensureObj(objId);
		obj.data = data;
		obj.resolve();
	}
	clear() {
		for (const objId in this.#objs) {
			const { data } = this.#objs[objId];
			data?.bitmap?.close();
		}
		this.#objs = Object.create(null);
	}
	*[Symbol.iterator]() {
		for (const objId in this.#objs) {
			const { data } = this.#objs[objId];
			if (data === INITIAL_DATA) continue;
			yield [objId, data];
		}
	}
};
var RenderTask = class {
	#internalRenderTask = null;
	constructor(internalRenderTask) {
		this.#internalRenderTask = internalRenderTask;
		this.onContinue = null;
	}
	get promise() {
		return this.#internalRenderTask.capability.promise;
	}
	cancel(extraDelay = 0) {
		this.#internalRenderTask.cancel(null, extraDelay);
	}
	get separateAnnots() {
		const { separateAnnots } = this.#internalRenderTask.operatorList;
		if (!separateAnnots) return false;
		const { annotationCanvasMap } = this.#internalRenderTask;
		return separateAnnots.form || separateAnnots.canvas && annotationCanvasMap?.size > 0;
	}
};
var InternalRenderTask = class InternalRenderTask {
	#rAF = null;
	static #canvasInUse = /* @__PURE__ */ new WeakSet();
	constructor({ callback, params, objs, commonObjs, annotationCanvasMap, operatorList, pageIndex, canvasFactory, filterFactory, useRequestAnimationFrame = false, pdfBug = false, pageColors = null }) {
		this.callback = callback;
		this.params = params;
		this.objs = objs;
		this.commonObjs = commonObjs;
		this.annotationCanvasMap = annotationCanvasMap;
		this.operatorListIdx = null;
		this.operatorList = operatorList;
		this._pageIndex = pageIndex;
		this.canvasFactory = canvasFactory;
		this.filterFactory = filterFactory;
		this._pdfBug = pdfBug;
		this.pageColors = pageColors;
		this.running = false;
		this.graphicsReadyCallback = null;
		this.graphicsReady = false;
		this._useRequestAnimationFrame = useRequestAnimationFrame === true && typeof window !== "undefined";
		this.cancelled = false;
		this.capability = Promise.withResolvers();
		this.task = new RenderTask(this);
		this._cancelBound = this.cancel.bind(this);
		this._continueBound = this._continue.bind(this);
		this._scheduleNextBound = this._scheduleNext.bind(this);
		this._nextBound = this._next.bind(this);
		this._canvas = params.canvasContext.canvas;
	}
	get completed() {
		return this.capability.promise.catch(function() {});
	}
	initializeGraphics({ transparency = false, optionalContentConfig }) {
		if (this.cancelled) return;
		if (this._canvas) {
			if (InternalRenderTask.#canvasInUse.has(this._canvas)) throw new Error("Cannot use the same canvas during multiple render() operations. Use different canvas or ensure previous operations were cancelled or completed.");
			InternalRenderTask.#canvasInUse.add(this._canvas);
		}
		if (this._pdfBug && globalThis.StepperManager?.enabled) {
			this.stepper = globalThis.StepperManager.create(this._pageIndex);
			this.stepper.init(this.operatorList);
			this.stepper.nextBreakPoint = this.stepper.getNextBreakPoint();
		}
		const { canvasContext, viewport, transform, background } = this.params;
		this.gfx = new CanvasGraphics(canvasContext, this.commonObjs, this.objs, this.canvasFactory, this.filterFactory, { optionalContentConfig }, this.annotationCanvasMap, this.pageColors);
		this.gfx.beginDrawing({
			transform,
			viewport,
			transparency,
			background
		});
		this.operatorListIdx = 0;
		this.graphicsReady = true;
		this.graphicsReadyCallback?.();
	}
	cancel(error = null, extraDelay = 0) {
		this.running = false;
		this.cancelled = true;
		this.gfx?.endDrawing();
		if (this.#rAF) {
			window.cancelAnimationFrame(this.#rAF);
			this.#rAF = null;
		}
		InternalRenderTask.#canvasInUse.delete(this._canvas);
		this.callback(error || new RenderingCancelledException$1(`Rendering cancelled, page ${this._pageIndex + 1}`, extraDelay));
	}
	operatorListChanged() {
		if (!this.graphicsReady) {
			this.graphicsReadyCallback ||= this._continueBound;
			return;
		}
		this.stepper?.updateOperatorList(this.operatorList);
		if (this.running) return;
		this._continue();
	}
	_continue() {
		this.running = true;
		if (this.cancelled) return;
		if (this.task.onContinue) this.task.onContinue(this._scheduleNextBound);
		else this._scheduleNext();
	}
	_scheduleNext() {
		if (this._useRequestAnimationFrame) this.#rAF = window.requestAnimationFrame(() => {
			this.#rAF = null;
			this._nextBound().catch(this._cancelBound);
		});
		else Promise.resolve().then(this._nextBound).catch(this._cancelBound);
	}
	async _next() {
		if (this.cancelled) return;
		this.operatorListIdx = this.gfx.executeOperatorList(this.operatorList, this.operatorListIdx, this._continueBound, this.stepper);
		if (this.operatorListIdx === this.operatorList.argsArray.length) {
			this.running = false;
			if (this.operatorList.lastChunk) {
				this.gfx.endDrawing();
				InternalRenderTask.#canvasInUse.delete(this._canvas);
				this.callback();
			}
		}
	}
};
var version$2 = "4.10.38";
var build$1 = "f9bea397f";
function makeColorComp(n) {
	return Math.floor(Math.max(0, Math.min(1, n)) * 255).toString(16).padStart(2, "0");
}
function scaleAndClamp(x) {
	return Math.max(0, Math.min(255, 255 * x));
}
var ColorConverters = class {
	static CMYK_G([c, y, m, k]) {
		return ["G", 1 - Math.min(1, .3 * c + .59 * m + .11 * y + k)];
	}
	static G_CMYK([g]) {
		return [
			"CMYK",
			0,
			0,
			0,
			1 - g
		];
	}
	static G_RGB([g]) {
		return [
			"RGB",
			g,
			g,
			g
		];
	}
	static G_rgb([g]) {
		g = scaleAndClamp(g);
		return [
			g,
			g,
			g
		];
	}
	static G_HTML([g]) {
		const G = makeColorComp(g);
		return `#${G}${G}${G}`;
	}
	static RGB_G([r, g, b]) {
		return ["G", .3 * r + .59 * g + .11 * b];
	}
	static RGB_rgb(color) {
		return color.map(scaleAndClamp);
	}
	static RGB_HTML(color) {
		return `#${color.map(makeColorComp).join("")}`;
	}
	static T_HTML() {
		return "#00000000";
	}
	static T_rgb() {
		return [null];
	}
	static CMYK_RGB([c, y, m, k]) {
		return [
			"RGB",
			1 - Math.min(1, c + k),
			1 - Math.min(1, m + k),
			1 - Math.min(1, y + k)
		];
	}
	static CMYK_rgb([c, y, m, k]) {
		return [
			scaleAndClamp(1 - Math.min(1, c + k)),
			scaleAndClamp(1 - Math.min(1, m + k)),
			scaleAndClamp(1 - Math.min(1, y + k))
		];
	}
	static CMYK_HTML(components) {
		const rgb = this.CMYK_RGB(components).slice(1);
		return this.RGB_HTML(rgb);
	}
	static RGB_CMYK([r, g, b]) {
		const c = 1 - r;
		const m = 1 - g;
		const y = 1 - b;
		return [
			"CMYK",
			c,
			m,
			y,
			Math.min(c, m, y)
		];
	}
};
var BaseSVGFactory = class {
	create(width, height, skipDimensions = false) {
		if (width <= 0 || height <= 0) throw new Error("Invalid SVG dimensions");
		const svg = this._createSVG("svg:svg");
		svg.setAttribute("version", "1.1");
		if (!skipDimensions) {
			svg.setAttribute("width", `${width}px`);
			svg.setAttribute("height", `${height}px`);
		}
		svg.setAttribute("preserveAspectRatio", "none");
		svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
		return svg;
	}
	createElement(type) {
		if (typeof type !== "string") throw new Error("Invalid SVG element type");
		return this._createSVG(type);
	}
	_createSVG(type) {
		unreachable("Abstract method `_createSVG` called.");
	}
};
var DOMSVGFactory$1 = class extends BaseSVGFactory {
	_createSVG(type) {
		return document.createElementNS(SVG_NS, type);
	}
};
var XfaLayer$1 = class {
	static setupStorage(html, id, element, storage, intent) {
		const storedData = storage.getValue(id, { value: null });
		switch (element.name) {
			case "textarea":
				if (storedData.value !== null) html.textContent = storedData.value;
				if (intent === "print") break;
				html.addEventListener("input", (event) => {
					storage.setValue(id, { value: event.target.value });
				});
				break;
			case "input":
				if (element.attributes.type === "radio" || element.attributes.type === "checkbox") {
					if (storedData.value === element.attributes.xfaOn) html.setAttribute("checked", true);
					else if (storedData.value === element.attributes.xfaOff) html.removeAttribute("checked");
					if (intent === "print") break;
					html.addEventListener("change", (event) => {
						storage.setValue(id, { value: event.target.checked ? event.target.getAttribute("xfaOn") : event.target.getAttribute("xfaOff") });
					});
				} else {
					if (storedData.value !== null) html.setAttribute("value", storedData.value);
					if (intent === "print") break;
					html.addEventListener("input", (event) => {
						storage.setValue(id, { value: event.target.value });
					});
				}
				break;
			case "select":
				if (storedData.value !== null) {
					html.setAttribute("value", storedData.value);
					for (const option of element.children) if (option.attributes.value === storedData.value) option.attributes.selected = true;
					else if (option.attributes.hasOwnProperty("selected")) delete option.attributes.selected;
				}
				html.addEventListener("input", (event) => {
					const options = event.target.options;
					const value = options.selectedIndex === -1 ? "" : options[options.selectedIndex].value;
					storage.setValue(id, { value });
				});
		}
	}
	static setAttributes({ html, element, storage = null, intent, linkService }) {
		const { attributes } = element;
		const isHTMLAnchorElement = html instanceof HTMLAnchorElement;
		if (attributes.type === "radio") attributes.name = `${attributes.name}-${intent}`;
		for (const [key, value] of Object.entries(attributes)) {
			if (value === null || value === void 0) continue;
			switch (key) {
				case "class":
					if (value.length) html.setAttribute(key, value.join(" "));
					break;
				case "dataId": break;
				case "id":
					html.setAttribute("data-element-id", value);
					break;
				case "style":
					Object.assign(html.style, value);
					break;
				case "textContent":
					html.textContent = value;
					break;
				default: if (!isHTMLAnchorElement || key !== "href" && key !== "newWindow") html.setAttribute(key, value);
			}
		}
		if (isHTMLAnchorElement) linkService.addLinkAttributes(html, attributes.href, attributes.newWindow);
		if (storage && attributes.dataId) this.setupStorage(html, attributes.dataId, element, storage);
	}
	static render(parameters) {
		const storage = parameters.annotationStorage;
		const linkService = parameters.linkService;
		const root = parameters.xfaHtml;
		const intent = parameters.intent || "display";
		const rootHtml = document.createElement(root.name);
		if (root.attributes) this.setAttributes({
			html: rootHtml,
			element: root,
			intent,
			linkService
		});
		const isNotForRichText = intent !== "richText";
		const rootDiv = parameters.div;
		rootDiv.append(rootHtml);
		if (parameters.viewport) {
			const transform = `matrix(${parameters.viewport.transform.join(",")})`;
			rootDiv.style.transform = transform;
		}
		if (isNotForRichText) rootDiv.setAttribute("class", "xfaLayer xfaFont");
		const textDivs = [];
		if (root.children.length === 0) {
			if (root.value) {
				const node = document.createTextNode(root.value);
				rootHtml.append(node);
				if (isNotForRichText && XfaText.shouldBuildText(root.name)) textDivs.push(node);
			}
			return { textDivs };
		}
		const stack = [[
			root,
			-1,
			rootHtml
		]];
		while (stack.length > 0) {
			const [parent, i, html] = stack.at(-1);
			if (i + 1 === parent.children.length) {
				stack.pop();
				continue;
			}
			const child = parent.children[++stack.at(-1)[1]];
			if (child === null) continue;
			const { name } = child;
			if (name === "#text") {
				const node = document.createTextNode(child.value);
				textDivs.push(node);
				html.append(node);
				continue;
			}
			const childHtml = child?.attributes?.xmlns ? document.createElementNS(child.attributes.xmlns, name) : document.createElement(name);
			html.append(childHtml);
			if (child.attributes) this.setAttributes({
				html: childHtml,
				element: child,
				storage,
				intent,
				linkService
			});
			if (child.children?.length > 0) stack.push([
				child,
				-1,
				childHtml
			]);
			else if (child.value) {
				const node = document.createTextNode(child.value);
				if (isNotForRichText && XfaText.shouldBuildText(name)) textDivs.push(node);
				childHtml.append(node);
			}
		}
		for (const el of rootDiv.querySelectorAll(".xfaNonInteractive input, .xfaNonInteractive textarea")) el.setAttribute("readOnly", true);
		return { textDivs };
	}
	static update(parameters) {
		const transform = `matrix(${parameters.viewport.transform.join(",")})`;
		parameters.div.style.transform = transform;
		parameters.div.hidden = false;
	}
};
var DEFAULT_TAB_INDEX = 1e3;
var annotation_layer_DEFAULT_FONT_SIZE = 9;
var GetElementsByNameSet = /* @__PURE__ */ new WeakSet();
function getRectDims(rect) {
	return {
		width: rect[2] - rect[0],
		height: rect[3] - rect[1]
	};
}
var AnnotationElementFactory = class {
	static create(parameters) {
		switch (parameters.data.annotationType) {
			case AnnotationType.LINK: return new LinkAnnotationElement(parameters);
			case AnnotationType.TEXT: return new TextAnnotationElement(parameters);
			case AnnotationType.WIDGET:
				switch (parameters.data.fieldType) {
					case "Tx": return new TextWidgetAnnotationElement(parameters);
					case "Btn":
						if (parameters.data.radioButton) return new RadioButtonWidgetAnnotationElement(parameters);
						else if (parameters.data.checkBox) return new CheckboxWidgetAnnotationElement(parameters);
						return new PushButtonWidgetAnnotationElement(parameters);
					case "Ch": return new ChoiceWidgetAnnotationElement(parameters);
					case "Sig": return new SignatureWidgetAnnotationElement(parameters);
				}
				return new WidgetAnnotationElement(parameters);
			case AnnotationType.POPUP: return new PopupAnnotationElement(parameters);
			case AnnotationType.FREETEXT: return new FreeTextAnnotationElement(parameters);
			case AnnotationType.LINE: return new LineAnnotationElement(parameters);
			case AnnotationType.SQUARE: return new SquareAnnotationElement(parameters);
			case AnnotationType.CIRCLE: return new CircleAnnotationElement(parameters);
			case AnnotationType.POLYLINE: return new PolylineAnnotationElement(parameters);
			case AnnotationType.CARET: return new CaretAnnotationElement(parameters);
			case AnnotationType.INK: return new InkAnnotationElement(parameters);
			case AnnotationType.POLYGON: return new PolygonAnnotationElement(parameters);
			case AnnotationType.HIGHLIGHT: return new HighlightAnnotationElement(parameters);
			case AnnotationType.UNDERLINE: return new UnderlineAnnotationElement(parameters);
			case AnnotationType.SQUIGGLY: return new SquigglyAnnotationElement(parameters);
			case AnnotationType.STRIKEOUT: return new StrikeOutAnnotationElement(parameters);
			case AnnotationType.STAMP: return new StampAnnotationElement(parameters);
			case AnnotationType.FILEATTACHMENT: return new FileAttachmentAnnotationElement(parameters);
			default: return new AnnotationElement(parameters);
		}
	}
};
var AnnotationElement = class AnnotationElement {
	#updates = null;
	#hasBorder = false;
	#popupElement = null;
	constructor(parameters, { isRenderable = false, ignoreBorder = false, createQuadrilaterals = false } = {}) {
		this.isRenderable = isRenderable;
		this.data = parameters.data;
		this.layer = parameters.layer;
		this.linkService = parameters.linkService;
		this.downloadManager = parameters.downloadManager;
		this.imageResourcesPath = parameters.imageResourcesPath;
		this.renderForms = parameters.renderForms;
		this.svgFactory = parameters.svgFactory;
		this.annotationStorage = parameters.annotationStorage;
		this.enableScripting = parameters.enableScripting;
		this.hasJSActions = parameters.hasJSActions;
		this._fieldObjects = parameters.fieldObjects;
		this.parent = parameters.parent;
		if (isRenderable) this.container = this._createContainer(ignoreBorder);
		if (createQuadrilaterals) this._createQuadrilaterals();
	}
	static _hasPopupData({ titleObj, contentsObj, richText }) {
		return !!(titleObj?.str || contentsObj?.str || richText?.str);
	}
	get _isEditable() {
		return this.data.isEditable;
	}
	get hasPopupData() {
		return AnnotationElement._hasPopupData(this.data);
	}
	updateEdited(params) {
		if (!this.container) return;
		this.#updates ||= { rect: this.data.rect.slice(0) };
		const { rect } = params;
		if (rect) this.#setRectEdited(rect);
		this.#popupElement?.popup.updateEdited(params);
	}
	resetEdited() {
		if (!this.#updates) return;
		this.#setRectEdited(this.#updates.rect);
		this.#popupElement?.popup.resetEdited();
		this.#updates = null;
	}
	#setRectEdited(rect) {
		const { container: { style }, data: { rect: currentRect, rotation }, parent: { viewport: { rawDims: { pageWidth, pageHeight, pageX, pageY } } } } = this;
		currentRect?.splice(0, 4, ...rect);
		const { width, height } = getRectDims(rect);
		style.left = `${100 * (rect[0] - pageX) / pageWidth}%`;
		style.top = `${100 * (pageHeight - rect[3] + pageY) / pageHeight}%`;
		if (rotation === 0) {
			style.width = `${100 * width / pageWidth}%`;
			style.height = `${100 * height / pageHeight}%`;
		} else this.setRotation(rotation);
	}
	_createContainer(ignoreBorder) {
		const { data, parent: { page, viewport } } = this;
		const container = document.createElement("section");
		container.setAttribute("data-annotation-id", data.id);
		if (!(this instanceof WidgetAnnotationElement)) container.tabIndex = DEFAULT_TAB_INDEX;
		const { style } = container;
		style.zIndex = this.parent.zIndex++;
		if (data.alternativeText) container.title = data.alternativeText;
		if (data.noRotate) container.classList.add("norotate");
		if (!data.rect || this instanceof PopupAnnotationElement) {
			const { rotation } = data;
			if (!data.hasOwnCanvas && rotation !== 0) this.setRotation(rotation, container);
			return container;
		}
		const { width, height } = getRectDims(data.rect);
		if (!ignoreBorder && data.borderStyle.width > 0) {
			style.borderWidth = `${data.borderStyle.width}px`;
			const horizontalRadius = data.borderStyle.horizontalCornerRadius;
			const verticalRadius = data.borderStyle.verticalCornerRadius;
			if (horizontalRadius > 0 || verticalRadius > 0) style.borderRadius = `calc(${horizontalRadius}px * var(--scale-factor)) / calc(${verticalRadius}px * var(--scale-factor))`;
			else if (this instanceof RadioButtonWidgetAnnotationElement) style.borderRadius = `calc(${width}px * var(--scale-factor)) / calc(${height}px * var(--scale-factor))`;
			switch (data.borderStyle.style) {
				case AnnotationBorderStyleType.SOLID:
					style.borderStyle = "solid";
					break;
				case AnnotationBorderStyleType.DASHED:
					style.borderStyle = "dashed";
					break;
				case AnnotationBorderStyleType.BEVELED:
					warn("Unimplemented border style: beveled");
					break;
				case AnnotationBorderStyleType.INSET:
					warn("Unimplemented border style: inset");
					break;
				case AnnotationBorderStyleType.UNDERLINE: style.borderBottomStyle = "solid";
			}
			const borderColor = data.borderColor || null;
			if (borderColor) {
				this.#hasBorder = true;
				style.borderColor = Util$1.makeHexColor(borderColor[0] | 0, borderColor[1] | 0, borderColor[2] | 0);
			} else style.borderWidth = 0;
		}
		const rect = Util$1.normalizeRect([
			data.rect[0],
			page.view[3] - data.rect[1] + page.view[1],
			data.rect[2],
			page.view[3] - data.rect[3] + page.view[1]
		]);
		const { pageWidth, pageHeight, pageX, pageY } = viewport.rawDims;
		style.left = `${100 * (rect[0] - pageX) / pageWidth}%`;
		style.top = `${100 * (rect[1] - pageY) / pageHeight}%`;
		const { rotation } = data;
		if (data.hasOwnCanvas || rotation === 0) {
			style.width = `${100 * width / pageWidth}%`;
			style.height = `${100 * height / pageHeight}%`;
		} else this.setRotation(rotation, container);
		return container;
	}
	setRotation(angle, container = this.container) {
		if (!this.data.rect) return;
		const { pageWidth, pageHeight } = this.parent.viewport.rawDims;
		const { width, height } = getRectDims(this.data.rect);
		let elementWidth, elementHeight;
		if (angle % 180 === 0) {
			elementWidth = 100 * width / pageWidth;
			elementHeight = 100 * height / pageHeight;
		} else {
			elementWidth = 100 * height / pageWidth;
			elementHeight = 100 * width / pageHeight;
		}
		container.style.width = `${elementWidth}%`;
		container.style.height = `${elementHeight}%`;
		container.setAttribute("data-main-rotation", (360 - angle) % 360);
	}
	get _commonActions() {
		const setColor = (jsName, styleName, event) => {
			const color = event.detail[jsName];
			const colorType = color[0];
			const colorArray = color.slice(1);
			event.target.style[styleName] = ColorConverters[`${colorType}_HTML`](colorArray);
			this.annotationStorage.setValue(this.data.id, { [styleName]: ColorConverters[`${colorType}_rgb`](colorArray) });
		};
		return shadow$1(this, "_commonActions", {
			display: (event) => {
				const { display } = event.detail;
				const hidden = display % 2 === 1;
				this.container.style.visibility = hidden ? "hidden" : "visible";
				this.annotationStorage.setValue(this.data.id, {
					noView: hidden,
					noPrint: display === 1 || display === 2
				});
			},
			print: (event) => {
				this.annotationStorage.setValue(this.data.id, { noPrint: !event.detail.print });
			},
			hidden: (event) => {
				const { hidden } = event.detail;
				this.container.style.visibility = hidden ? "hidden" : "visible";
				this.annotationStorage.setValue(this.data.id, {
					noPrint: hidden,
					noView: hidden
				});
			},
			focus: (event) => {
				setTimeout(() => event.target.focus({ preventScroll: false }), 0);
			},
			userName: (event) => {
				event.target.title = event.detail.userName;
			},
			readonly: (event) => {
				event.target.disabled = event.detail.readonly;
			},
			required: (event) => {
				this._setRequired(event.target, event.detail.required);
			},
			bgColor: (event) => {
				setColor("bgColor", "backgroundColor", event);
			},
			fillColor: (event) => {
				setColor("fillColor", "backgroundColor", event);
			},
			fgColor: (event) => {
				setColor("fgColor", "color", event);
			},
			textColor: (event) => {
				setColor("textColor", "color", event);
			},
			borderColor: (event) => {
				setColor("borderColor", "borderColor", event);
			},
			strokeColor: (event) => {
				setColor("strokeColor", "borderColor", event);
			},
			rotation: (event) => {
				const angle = event.detail.rotation;
				this.setRotation(angle);
				this.annotationStorage.setValue(this.data.id, { rotation: angle });
			}
		});
	}
	_dispatchEventFromSandbox(actions, jsEvent) {
		const commonActions = this._commonActions;
		for (const name of Object.keys(jsEvent.detail)) (actions[name] || commonActions[name])?.(jsEvent);
	}
	_setDefaultPropertiesFromJS(element) {
		if (!this.enableScripting) return;
		const storedData = this.annotationStorage.getRawValue(this.data.id);
		if (!storedData) return;
		const commonActions = this._commonActions;
		for (const [actionName, detail] of Object.entries(storedData)) {
			const action = commonActions[actionName];
			if (action) {
				action({
					detail: { [actionName]: detail },
					target: element
				});
				delete storedData[actionName];
			}
		}
	}
	_createQuadrilaterals() {
		if (!this.container) return;
		const { quadPoints } = this.data;
		if (!quadPoints) return;
		const [rectBlX, rectBlY, rectTrX, rectTrY] = this.data.rect.map((x) => Math.fround(x));
		if (quadPoints.length === 8) {
			const [trX, trY, blX, blY] = quadPoints.subarray(2, 6);
			if (rectTrX === trX && rectTrY === trY && rectBlX === blX && rectBlY === blY) return;
		}
		const { style } = this.container;
		let svgBuffer;
		if (this.#hasBorder) {
			const { borderColor, borderWidth } = style;
			style.borderWidth = 0;
			svgBuffer = [
				"url('data:image/svg+xml;utf8,",
				`<svg xmlns="http://www.w3.org/2000/svg"`,
				` preserveAspectRatio="none" viewBox="0 0 1 1">`,
				`<g fill="transparent" stroke="${borderColor}" stroke-width="${borderWidth}">`
			];
			this.container.classList.add("hasBorder");
		}
		const width = rectTrX - rectBlX;
		const height = rectTrY - rectBlY;
		const { svgFactory } = this;
		const svg = svgFactory.createElement("svg");
		svg.classList.add("quadrilateralsContainer");
		svg.setAttribute("width", 0);
		svg.setAttribute("height", 0);
		const defs = svgFactory.createElement("defs");
		svg.append(defs);
		const clipPath = svgFactory.createElement("clipPath");
		const id = `clippath_${this.data.id}`;
		clipPath.setAttribute("id", id);
		clipPath.setAttribute("clipPathUnits", "objectBoundingBox");
		defs.append(clipPath);
		for (let i = 2, ii = quadPoints.length; i < ii; i += 8) {
			const trX = quadPoints[i];
			const trY = quadPoints[i + 1];
			const blX = quadPoints[i + 2];
			const blY = quadPoints[i + 3];
			const rect = svgFactory.createElement("rect");
			const x = (blX - rectBlX) / width;
			const y = (rectTrY - trY) / height;
			const rectWidth = (trX - blX) / width;
			const rectHeight = (trY - blY) / height;
			rect.setAttribute("x", x);
			rect.setAttribute("y", y);
			rect.setAttribute("width", rectWidth);
			rect.setAttribute("height", rectHeight);
			clipPath.append(rect);
			svgBuffer?.push(`<rect vector-effect="non-scaling-stroke" x="${x}" y="${y}" width="${rectWidth}" height="${rectHeight}"/>`);
		}
		if (this.#hasBorder) {
			svgBuffer.push(`</g></svg>')`);
			style.backgroundImage = svgBuffer.join("");
		}
		this.container.append(svg);
		this.container.style.clipPath = `url(#${id})`;
	}
	_createPopup() {
		const { data } = this;
		const popup = this.#popupElement = new PopupAnnotationElement({
			data: {
				color: data.color,
				titleObj: data.titleObj,
				modificationDate: data.modificationDate,
				contentsObj: data.contentsObj,
				richText: data.richText,
				parentRect: data.rect,
				borderStyle: 0,
				id: `popup_${data.id}`,
				rotation: data.rotation
			},
			parent: this.parent,
			elements: [this]
		});
		this.parent.div.append(popup.render());
	}
	render() {
		unreachable("Abstract method `AnnotationElement.render` called");
	}
	_getElementsByName(name, skipId = null) {
		const fields = [];
		if (this._fieldObjects) {
			const fieldObj = this._fieldObjects[name];
			if (fieldObj) for (const { page, id, exportValues } of fieldObj) {
				if (page === -1) continue;
				if (id === skipId) continue;
				const exportValue = typeof exportValues === "string" ? exportValues : null;
				const domElement = document.querySelector(`[data-element-id="${id}"]`);
				if (domElement && !GetElementsByNameSet.has(domElement)) {
					warn(`_getElementsByName - element not allowed: ${id}`);
					continue;
				}
				fields.push({
					id,
					exportValue,
					domElement
				});
			}
			return fields;
		}
		for (const domElement of document.getElementsByName(name)) {
			const { exportValue } = domElement;
			const id = domElement.getAttribute("data-element-id");
			if (id === skipId) continue;
			if (!GetElementsByNameSet.has(domElement)) continue;
			fields.push({
				id,
				exportValue,
				domElement
			});
		}
		return fields;
	}
	show() {
		if (this.container) this.container.hidden = false;
		this.popup?.maybeShow();
	}
	hide() {
		if (this.container) this.container.hidden = true;
		this.popup?.forceHide();
	}
	getElementsToTriggerPopup() {
		return this.container;
	}
	addHighlightArea() {
		const triggers = this.getElementsToTriggerPopup();
		if (Array.isArray(triggers)) for (const element of triggers) element.classList.add("highlightArea");
		else triggers.classList.add("highlightArea");
	}
	_editOnDoubleClick() {
		if (!this._isEditable) return;
		const { annotationEditorType: mode, data: { id: editId } } = this;
		this.container.addEventListener("dblclick", () => {
			this.linkService.eventBus?.dispatch("switchannotationeditormode", {
				source: this,
				mode,
				editId
			});
		});
	}
};
var LinkAnnotationElement = class extends AnnotationElement {
	constructor(parameters, options = null) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: !!options?.ignoreBorder,
			createQuadrilaterals: true
		});
		this.isTooltipOnly = parameters.data.isTooltipOnly;
	}
	render() {
		const { data, linkService } = this;
		const link = document.createElement("a");
		link.setAttribute("data-element-id", data.id);
		let isBound = false;
		if (data.url) {
			linkService.addLinkAttributes(link, data.url, data.newWindow);
			isBound = true;
		} else if (data.action) {
			this._bindNamedAction(link, data.action);
			isBound = true;
		} else if (data.attachment) {
			this.#bindAttachment(link, data.attachment, data.attachmentDest);
			isBound = true;
		} else if (data.setOCGState) {
			this.#bindSetOCGState(link, data.setOCGState);
			isBound = true;
		} else if (data.dest) {
			this._bindLink(link, data.dest);
			isBound = true;
		} else {
			if (data.actions && (data.actions.Action || data.actions["Mouse Up"] || data.actions["Mouse Down"]) && this.enableScripting && this.hasJSActions) {
				this._bindJSAction(link, data);
				isBound = true;
			}
			if (data.resetForm) {
				this._bindResetFormAction(link, data.resetForm);
				isBound = true;
			} else if (this.isTooltipOnly && !isBound) {
				this._bindLink(link, "");
				isBound = true;
			}
		}
		this.container.classList.add("linkAnnotation");
		if (isBound) this.container.append(link);
		return this.container;
	}
	#setInternalLink() {
		this.container.setAttribute("data-internal-link", "");
	}
	_bindLink(link, destination) {
		link.href = this.linkService.getDestinationHash(destination);
		link.onclick = () => {
			if (destination) this.linkService.goToDestination(destination);
			return false;
		};
		if (destination || destination === "") this.#setInternalLink();
	}
	_bindNamedAction(link, action) {
		link.href = this.linkService.getAnchorUrl("");
		link.onclick = () => {
			this.linkService.executeNamedAction(action);
			return false;
		};
		this.#setInternalLink();
	}
	#bindAttachment(link, attachment, dest = null) {
		link.href = this.linkService.getAnchorUrl("");
		if (attachment.description) link.title = attachment.description;
		link.onclick = () => {
			this.downloadManager?.openOrDownloadData(attachment.content, attachment.filename, dest);
			return false;
		};
		this.#setInternalLink();
	}
	#bindSetOCGState(link, action) {
		link.href = this.linkService.getAnchorUrl("");
		link.onclick = () => {
			this.linkService.executeSetOCGState(action);
			return false;
		};
		this.#setInternalLink();
	}
	_bindJSAction(link, data) {
		link.href = this.linkService.getAnchorUrl("");
		const map = /* @__PURE__ */ new Map([
			["Action", "onclick"],
			["Mouse Up", "onmouseup"],
			["Mouse Down", "onmousedown"]
		]);
		for (const name of Object.keys(data.actions)) {
			const jsName = map.get(name);
			if (!jsName) continue;
			link[jsName] = () => {
				this.linkService.eventBus?.dispatch("dispatcheventinsandbox", {
					source: this,
					detail: {
						id: data.id,
						name
					}
				});
				return false;
			};
		}
		if (!link.onclick) link.onclick = () => false;
		this.#setInternalLink();
	}
	_bindResetFormAction(link, resetForm) {
		const otherClickAction = link.onclick;
		if (!otherClickAction) link.href = this.linkService.getAnchorUrl("");
		this.#setInternalLink();
		if (!this._fieldObjects) {
			warn("_bindResetFormAction - \"resetForm\" action not supported, ensure that the `fieldObjects` parameter is provided.");
			if (!otherClickAction) link.onclick = () => false;
			return;
		}
		link.onclick = () => {
			otherClickAction?.();
			const { fields: resetFormFields, refs: resetFormRefs, include } = resetForm;
			const allFields = [];
			if (resetFormFields.length !== 0 || resetFormRefs.length !== 0) {
				const fieldIds = new Set(resetFormRefs);
				for (const fieldName of resetFormFields) {
					const fields = this._fieldObjects[fieldName] || [];
					for (const { id } of fields) fieldIds.add(id);
				}
				for (const fields of Object.values(this._fieldObjects)) for (const field of fields) if (fieldIds.has(field.id) === include) allFields.push(field);
			} else for (const fields of Object.values(this._fieldObjects)) allFields.push(...fields);
			const storage = this.annotationStorage;
			const allIds = [];
			for (const field of allFields) {
				const { id } = field;
				allIds.push(id);
				switch (field.type) {
					case "text": {
						const value = field.defaultValue || "";
						storage.setValue(id, { value });
						break;
					}
					case "checkbox":
					case "radiobutton": {
						const value = field.defaultValue === field.exportValues;
						storage.setValue(id, { value });
						break;
					}
					case "combobox":
					case "listbox": {
						const value = field.defaultValue || "";
						storage.setValue(id, { value });
						break;
					}
					default: continue;
				}
				const domElement = document.querySelector(`[data-element-id="${id}"]`);
				if (!domElement) continue;
				else if (!GetElementsByNameSet.has(domElement)) {
					warn(`_bindResetFormAction - element not allowed: ${id}`);
					continue;
				}
				domElement.dispatchEvent(new Event("resetform"));
			}
			if (this.enableScripting) this.linkService.eventBus?.dispatch("dispatcheventinsandbox", {
				source: this,
				detail: {
					id: "app",
					ids: allIds,
					name: "ResetForm"
				}
			});
			return false;
		};
	}
};
var TextAnnotationElement = class extends AnnotationElement {
	constructor(parameters) {
		super(parameters, { isRenderable: true });
	}
	render() {
		this.container.classList.add("textAnnotation");
		const image = document.createElement("img");
		image.src = this.imageResourcesPath + "annotation-" + this.data.name.toLowerCase() + ".svg";
		image.setAttribute("data-l10n-id", "pdfjs-text-annotation-type");
		image.setAttribute("data-l10n-args", JSON.stringify({ type: this.data.name }));
		if (!this.data.popupRef && this.hasPopupData) this._createPopup();
		this.container.append(image);
		return this.container;
	}
};
var WidgetAnnotationElement = class extends AnnotationElement {
	render() {
		return this.container;
	}
	showElementAndHideCanvas(element) {
		if (this.data.hasOwnCanvas) {
			if (element.previousSibling?.nodeName === "CANVAS") element.previousSibling.hidden = true;
			element.hidden = false;
		}
	}
	_getKeyModifier(event) {
		return util_FeatureTest.platform.isMac ? event.metaKey : event.ctrlKey;
	}
	_setEventListener(element, elementData, baseName, eventName, valueGetter) {
		if (baseName.includes("mouse")) element.addEventListener(baseName, (event) => {
			this.linkService.eventBus?.dispatch("dispatcheventinsandbox", {
				source: this,
				detail: {
					id: this.data.id,
					name: eventName,
					value: valueGetter(event),
					shift: event.shiftKey,
					modifier: this._getKeyModifier(event)
				}
			});
		});
		else element.addEventListener(baseName, (event) => {
			if (baseName === "blur") {
				if (!elementData.focused || !event.relatedTarget) return;
				elementData.focused = false;
			} else if (baseName === "focus") {
				if (elementData.focused) return;
				elementData.focused = true;
			}
			if (!valueGetter) return;
			this.linkService.eventBus?.dispatch("dispatcheventinsandbox", {
				source: this,
				detail: {
					id: this.data.id,
					name: eventName,
					value: valueGetter(event)
				}
			});
		});
	}
	_setEventListeners(element, elementData, names, getter) {
		for (const [baseName, eventName] of names) if (eventName === "Action" || this.data.actions?.[eventName]) {
			if (eventName === "Focus" || eventName === "Blur") elementData ||= { focused: false };
			this._setEventListener(element, elementData, baseName, eventName, getter);
			if (eventName === "Focus" && !this.data.actions?.Blur) this._setEventListener(element, elementData, "blur", "Blur", null);
			else if (eventName === "Blur" && !this.data.actions?.Focus) this._setEventListener(element, elementData, "focus", "Focus", null);
		}
	}
	_setBackgroundColor(element) {
		const color = this.data.backgroundColor || null;
		element.style.backgroundColor = color === null ? "transparent" : Util$1.makeHexColor(color[0], color[1], color[2]);
	}
	_setTextStyle(element) {
		const TEXT_ALIGNMENT = [
			"left",
			"center",
			"right"
		];
		const { fontColor } = this.data.defaultAppearanceData;
		const fontSize = this.data.defaultAppearanceData.fontSize || annotation_layer_DEFAULT_FONT_SIZE;
		const style = element.style;
		let computedFontSize;
		const BORDER_SIZE = 2;
		const roundToOneDecimal = (x) => Math.round(10 * x) / 10;
		if (this.data.multiLine) {
			const height = Math.abs(this.data.rect[3] - this.data.rect[1] - BORDER_SIZE);
			const lineHeight = height / (Math.round(height / (LINE_FACTOR * fontSize)) || 1);
			computedFontSize = Math.min(fontSize, roundToOneDecimal(lineHeight / LINE_FACTOR));
		} else {
			const height = Math.abs(this.data.rect[3] - this.data.rect[1] - BORDER_SIZE);
			computedFontSize = Math.min(fontSize, roundToOneDecimal(height / LINE_FACTOR));
		}
		style.fontSize = `calc(${computedFontSize}px * var(--scale-factor))`;
		style.color = Util$1.makeHexColor(fontColor[0], fontColor[1], fontColor[2]);
		if (this.data.textAlignment !== null) style.textAlign = TEXT_ALIGNMENT[this.data.textAlignment];
	}
	_setRequired(element, isRequired) {
		if (isRequired) element.setAttribute("required", true);
		else element.removeAttribute("required");
		element.setAttribute("aria-required", isRequired);
	}
};
var TextWidgetAnnotationElement = class extends WidgetAnnotationElement {
	constructor(parameters) {
		const isRenderable = parameters.renderForms || parameters.data.hasOwnCanvas || !parameters.data.hasAppearance && !!parameters.data.fieldValue;
		super(parameters, { isRenderable });
	}
	setPropertyOnSiblings(base, key, value, keyInStorage) {
		const storage = this.annotationStorage;
		for (const element of this._getElementsByName(base.name, base.id)) {
			if (element.domElement) element.domElement[key] = value;
			storage.setValue(element.id, { [keyInStorage]: value });
		}
	}
	render() {
		const storage = this.annotationStorage;
		const id = this.data.id;
		this.container.classList.add("textWidgetAnnotation");
		let element = null;
		if (this.renderForms) {
			const storedData = storage.getValue(id, { value: this.data.fieldValue });
			let textContent = storedData.value || "";
			const maxLen = storage.getValue(id, { charLimit: this.data.maxLen }).charLimit;
			if (maxLen && textContent.length > maxLen) textContent = textContent.slice(0, maxLen);
			let fieldFormattedValues = storedData.formattedValue || this.data.textContent?.join("\n") || null;
			if (fieldFormattedValues && this.data.comb) fieldFormattedValues = fieldFormattedValues.replaceAll(/\s+/g, "");
			const elementData = {
				userValue: textContent,
				formattedValue: fieldFormattedValues,
				lastCommittedValue: null,
				commitKey: 1,
				focused: false
			};
			if (this.data.multiLine) {
				element = document.createElement("textarea");
				element.textContent = fieldFormattedValues ?? textContent;
				if (this.data.doNotScroll) element.style.overflowY = "hidden";
			} else {
				element = document.createElement("input");
				element.type = "text";
				element.setAttribute("value", fieldFormattedValues ?? textContent);
				if (this.data.doNotScroll) element.style.overflowX = "hidden";
			}
			if (this.data.hasOwnCanvas) element.hidden = true;
			GetElementsByNameSet.add(element);
			element.setAttribute("data-element-id", id);
			element.disabled = this.data.readOnly;
			element.name = this.data.fieldName;
			element.tabIndex = DEFAULT_TAB_INDEX;
			this._setRequired(element, this.data.required);
			if (maxLen) element.maxLength = maxLen;
			element.addEventListener("input", (event) => {
				storage.setValue(id, { value: event.target.value });
				this.setPropertyOnSiblings(element, "value", event.target.value, "value");
				elementData.formattedValue = null;
			});
			element.addEventListener("resetform", (event) => {
				const defaultValue = this.data.defaultFieldValue ?? "";
				element.value = elementData.userValue = defaultValue;
				elementData.formattedValue = null;
			});
			let blurListener = (event) => {
				const { formattedValue } = elementData;
				if (formattedValue !== null && formattedValue !== void 0) event.target.value = formattedValue;
				event.target.scrollLeft = 0;
			};
			if (this.enableScripting && this.hasJSActions) {
				element.addEventListener("focus", (event) => {
					if (elementData.focused) return;
					const { target } = event;
					if (elementData.userValue) target.value = elementData.userValue;
					elementData.lastCommittedValue = target.value;
					elementData.commitKey = 1;
					if (!this.data.actions?.Focus) elementData.focused = true;
				});
				element.addEventListener("updatefromsandbox", (jsEvent) => {
					this.showElementAndHideCanvas(jsEvent.target);
					this._dispatchEventFromSandbox({
						value(event) {
							elementData.userValue = event.detail.value ?? "";
							storage.setValue(id, { value: elementData.userValue.toString() });
							event.target.value = elementData.userValue;
						},
						formattedValue(event) {
							const { formattedValue } = event.detail;
							elementData.formattedValue = formattedValue;
							if (formattedValue !== null && formattedValue !== void 0 && event.target !== document.activeElement) event.target.value = formattedValue;
							storage.setValue(id, { formattedValue });
						},
						selRange(event) {
							event.target.setSelectionRange(...event.detail.selRange);
						},
						charLimit: (event) => {
							const { charLimit } = event.detail;
							const { target } = event;
							if (charLimit === 0) {
								target.removeAttribute("maxLength");
								return;
							}
							target.setAttribute("maxLength", charLimit);
							let value = elementData.userValue;
							if (!value || value.length <= charLimit) return;
							value = value.slice(0, charLimit);
							target.value = elementData.userValue = value;
							storage.setValue(id, { value });
							this.linkService.eventBus?.dispatch("dispatcheventinsandbox", {
								source: this,
								detail: {
									id,
									name: "Keystroke",
									value,
									willCommit: true,
									commitKey: 1,
									selStart: target.selectionStart,
									selEnd: target.selectionEnd
								}
							});
						}
					}, jsEvent);
				});
				element.addEventListener("keydown", (event) => {
					elementData.commitKey = 1;
					let commitKey = -1;
					if (event.key === "Escape") commitKey = 0;
					else if (event.key === "Enter" && !this.data.multiLine) commitKey = 2;
					else if (event.key === "Tab") elementData.commitKey = 3;
					if (commitKey === -1) return;
					const { value } = event.target;
					if (elementData.lastCommittedValue === value) return;
					elementData.lastCommittedValue = value;
					elementData.userValue = value;
					this.linkService.eventBus?.dispatch("dispatcheventinsandbox", {
						source: this,
						detail: {
							id,
							name: "Keystroke",
							value,
							willCommit: true,
							commitKey,
							selStart: event.target.selectionStart,
							selEnd: event.target.selectionEnd
						}
					});
				});
				const _blurListener = blurListener;
				blurListener = null;
				element.addEventListener("blur", (event) => {
					if (!elementData.focused || !event.relatedTarget) return;
					if (!this.data.actions?.Blur) elementData.focused = false;
					const { value } = event.target;
					elementData.userValue = value;
					if (elementData.lastCommittedValue !== value) this.linkService.eventBus?.dispatch("dispatcheventinsandbox", {
						source: this,
						detail: {
							id,
							name: "Keystroke",
							value,
							willCommit: true,
							commitKey: elementData.commitKey,
							selStart: event.target.selectionStart,
							selEnd: event.target.selectionEnd
						}
					});
					_blurListener(event);
				});
				if (this.data.actions?.Keystroke) element.addEventListener("beforeinput", (event) => {
					elementData.lastCommittedValue = null;
					const { data, target } = event;
					const { value, selectionStart, selectionEnd } = target;
					let selStart = selectionStart, selEnd = selectionEnd;
					switch (event.inputType) {
						case "deleteWordBackward": {
							const match = value.substring(0, selectionStart).match(/\w*[^\w]*$/);
							if (match) selStart -= match[0].length;
							break;
						}
						case "deleteWordForward": {
							const match = value.substring(selectionStart).match(/^[^\w]*\w*/);
							if (match) selEnd += match[0].length;
							break;
						}
						case "deleteContentBackward":
							if (selectionStart === selectionEnd) selStart -= 1;
							break;
						case "deleteContentForward": if (selectionStart === selectionEnd) selEnd += 1;
					}
					event.preventDefault();
					this.linkService.eventBus?.dispatch("dispatcheventinsandbox", {
						source: this,
						detail: {
							id,
							name: "Keystroke",
							value,
							change: data || "",
							willCommit: false,
							selStart,
							selEnd
						}
					});
				});
				this._setEventListeners(element, elementData, [
					["focus", "Focus"],
					["blur", "Blur"],
					["mousedown", "Mouse Down"],
					["mouseenter", "Mouse Enter"],
					["mouseleave", "Mouse Exit"],
					["mouseup", "Mouse Up"]
				], (event) => event.target.value);
			}
			if (blurListener) element.addEventListener("blur", blurListener);
			if (this.data.comb) {
				const combWidth = (this.data.rect[2] - this.data.rect[0]) / maxLen;
				element.classList.add("comb");
				element.style.letterSpacing = `calc(${combWidth}px * var(--scale-factor) - 1ch)`;
			}
		} else {
			element = document.createElement("div");
			element.textContent = this.data.fieldValue;
			element.style.verticalAlign = "middle";
			element.style.display = "table-cell";
			if (this.data.hasOwnCanvas) element.hidden = true;
		}
		this._setTextStyle(element);
		this._setBackgroundColor(element);
		this._setDefaultPropertiesFromJS(element);
		this.container.append(element);
		return this.container;
	}
};
var SignatureWidgetAnnotationElement = class extends WidgetAnnotationElement {
	constructor(parameters) {
		super(parameters, { isRenderable: !!parameters.data.hasOwnCanvas });
	}
};
var CheckboxWidgetAnnotationElement = class extends WidgetAnnotationElement {
	constructor(parameters) {
		super(parameters, { isRenderable: parameters.renderForms });
	}
	render() {
		const storage = this.annotationStorage;
		const data = this.data;
		const id = data.id;
		let value = storage.getValue(id, { value: data.exportValue === data.fieldValue }).value;
		if (typeof value === "string") {
			value = value !== "Off";
			storage.setValue(id, { value });
		}
		this.container.classList.add("buttonWidgetAnnotation", "checkBox");
		const element = document.createElement("input");
		GetElementsByNameSet.add(element);
		element.setAttribute("data-element-id", id);
		element.disabled = data.readOnly;
		this._setRequired(element, this.data.required);
		element.type = "checkbox";
		element.name = data.fieldName;
		if (value) element.setAttribute("checked", true);
		element.setAttribute("exportValue", data.exportValue);
		element.tabIndex = DEFAULT_TAB_INDEX;
		element.addEventListener("change", (event) => {
			const { name, checked } = event.target;
			for (const checkbox of this._getElementsByName(name, id)) {
				const curChecked = checked && checkbox.exportValue === data.exportValue;
				if (checkbox.domElement) checkbox.domElement.checked = curChecked;
				storage.setValue(checkbox.id, { value: curChecked });
			}
			storage.setValue(id, { value: checked });
		});
		element.addEventListener("resetform", (event) => {
			const defaultValue = data.defaultFieldValue || "Off";
			event.target.checked = defaultValue === data.exportValue;
		});
		if (this.enableScripting && this.hasJSActions) {
			element.addEventListener("updatefromsandbox", (jsEvent) => {
				this._dispatchEventFromSandbox({ value(event) {
					event.target.checked = event.detail.value !== "Off";
					storage.setValue(id, { value: event.target.checked });
				} }, jsEvent);
			});
			this._setEventListeners(element, null, [
				["change", "Validate"],
				["change", "Action"],
				["focus", "Focus"],
				["blur", "Blur"],
				["mousedown", "Mouse Down"],
				["mouseenter", "Mouse Enter"],
				["mouseleave", "Mouse Exit"],
				["mouseup", "Mouse Up"]
			], (event) => event.target.checked);
		}
		this._setBackgroundColor(element);
		this._setDefaultPropertiesFromJS(element);
		this.container.append(element);
		return this.container;
	}
};
var RadioButtonWidgetAnnotationElement = class extends WidgetAnnotationElement {
	constructor(parameters) {
		super(parameters, { isRenderable: parameters.renderForms });
	}
	render() {
		this.container.classList.add("buttonWidgetAnnotation", "radioButton");
		const storage = this.annotationStorage;
		const data = this.data;
		const id = data.id;
		let value = storage.getValue(id, { value: data.fieldValue === data.buttonValue }).value;
		if (typeof value === "string") {
			value = value !== data.buttonValue;
			storage.setValue(id, { value });
		}
		if (value) for (const radio of this._getElementsByName(data.fieldName, id)) storage.setValue(radio.id, { value: false });
		const element = document.createElement("input");
		GetElementsByNameSet.add(element);
		element.setAttribute("data-element-id", id);
		element.disabled = data.readOnly;
		this._setRequired(element, this.data.required);
		element.type = "radio";
		element.name = data.fieldName;
		if (value) element.setAttribute("checked", true);
		element.tabIndex = DEFAULT_TAB_INDEX;
		element.addEventListener("change", (event) => {
			const { name, checked } = event.target;
			for (const radio of this._getElementsByName(name, id)) storage.setValue(radio.id, { value: false });
			storage.setValue(id, { value: checked });
		});
		element.addEventListener("resetform", (event) => {
			const defaultValue = data.defaultFieldValue;
			event.target.checked = defaultValue !== null && defaultValue !== void 0 && defaultValue === data.buttonValue;
		});
		if (this.enableScripting && this.hasJSActions) {
			const pdfButtonValue = data.buttonValue;
			element.addEventListener("updatefromsandbox", (jsEvent) => {
				this._dispatchEventFromSandbox({ value: (event) => {
					const checked = pdfButtonValue === event.detail.value;
					for (const radio of this._getElementsByName(event.target.name)) {
						const curChecked = checked && radio.id === id;
						if (radio.domElement) radio.domElement.checked = curChecked;
						storage.setValue(radio.id, { value: curChecked });
					}
				} }, jsEvent);
			});
			this._setEventListeners(element, null, [
				["change", "Validate"],
				["change", "Action"],
				["focus", "Focus"],
				["blur", "Blur"],
				["mousedown", "Mouse Down"],
				["mouseenter", "Mouse Enter"],
				["mouseleave", "Mouse Exit"],
				["mouseup", "Mouse Up"]
			], (event) => event.target.checked);
		}
		this._setBackgroundColor(element);
		this._setDefaultPropertiesFromJS(element);
		this.container.append(element);
		return this.container;
	}
};
var PushButtonWidgetAnnotationElement = class extends LinkAnnotationElement {
	constructor(parameters) {
		super(parameters, { ignoreBorder: parameters.data.hasAppearance });
	}
	render() {
		const container = super.render();
		container.classList.add("buttonWidgetAnnotation", "pushButton");
		const linkElement = container.lastChild;
		if (this.enableScripting && this.hasJSActions && linkElement) {
			this._setDefaultPropertiesFromJS(linkElement);
			linkElement.addEventListener("updatefromsandbox", (jsEvent) => {
				this._dispatchEventFromSandbox({}, jsEvent);
			});
		}
		return container;
	}
};
var ChoiceWidgetAnnotationElement = class extends WidgetAnnotationElement {
	constructor(parameters) {
		super(parameters, { isRenderable: parameters.renderForms });
	}
	render() {
		this.container.classList.add("choiceWidgetAnnotation");
		const storage = this.annotationStorage;
		const id = this.data.id;
		const storedData = storage.getValue(id, { value: this.data.fieldValue });
		const selectElement = document.createElement("select");
		GetElementsByNameSet.add(selectElement);
		selectElement.setAttribute("data-element-id", id);
		selectElement.disabled = this.data.readOnly;
		this._setRequired(selectElement, this.data.required);
		selectElement.name = this.data.fieldName;
		selectElement.tabIndex = DEFAULT_TAB_INDEX;
		let addAnEmptyEntry = this.data.combo && this.data.options.length > 0;
		if (!this.data.combo) {
			selectElement.size = this.data.options.length;
			if (this.data.multiSelect) selectElement.multiple = true;
		}
		selectElement.addEventListener("resetform", (event) => {
			const defaultValue = this.data.defaultFieldValue;
			for (const option of selectElement.options) option.selected = option.value === defaultValue;
		});
		for (const option of this.data.options) {
			const optionElement = document.createElement("option");
			optionElement.textContent = option.displayValue;
			optionElement.value = option.exportValue;
			if (storedData.value.includes(option.exportValue)) {
				optionElement.setAttribute("selected", true);
				addAnEmptyEntry = false;
			}
			selectElement.append(optionElement);
		}
		let removeEmptyEntry = null;
		if (addAnEmptyEntry) {
			const noneOptionElement = document.createElement("option");
			noneOptionElement.value = " ";
			noneOptionElement.setAttribute("hidden", true);
			noneOptionElement.setAttribute("selected", true);
			selectElement.prepend(noneOptionElement);
			removeEmptyEntry = () => {
				noneOptionElement.remove();
				selectElement.removeEventListener("input", removeEmptyEntry);
				removeEmptyEntry = null;
			};
			selectElement.addEventListener("input", removeEmptyEntry);
		}
		const getValue = (isExport) => {
			const name = isExport ? "value" : "textContent";
			const { options, multiple } = selectElement;
			if (!multiple) return options.selectedIndex === -1 ? null : options[options.selectedIndex][name];
			return Array.prototype.filter.call(options, (option) => option.selected).map((option) => option[name]);
		};
		let selectedValues = getValue(false);
		const getItems = (event) => {
			const options = event.target.options;
			return Array.prototype.map.call(options, (option) => ({
				displayValue: option.textContent,
				exportValue: option.value
			}));
		};
		if (this.enableScripting && this.hasJSActions) {
			selectElement.addEventListener("updatefromsandbox", (jsEvent) => {
				this._dispatchEventFromSandbox({
					value(event) {
						removeEmptyEntry?.();
						const value = event.detail.value;
						const values = new Set(Array.isArray(value) ? value : [value]);
						for (const option of selectElement.options) option.selected = values.has(option.value);
						storage.setValue(id, { value: getValue(true) });
						selectedValues = getValue(false);
					},
					multipleSelection(event) {
						selectElement.multiple = true;
					},
					remove(event) {
						const options = selectElement.options;
						const index = event.detail.remove;
						options[index].selected = false;
						selectElement.remove(index);
						if (options.length > 0) {
							if (Array.prototype.findIndex.call(options, (option) => option.selected) === -1) options[0].selected = true;
						}
						storage.setValue(id, {
							value: getValue(true),
							items: getItems(event)
						});
						selectedValues = getValue(false);
					},
					clear(event) {
						while (selectElement.length !== 0) selectElement.remove(0);
						storage.setValue(id, {
							value: null,
							items: []
						});
						selectedValues = getValue(false);
					},
					insert(event) {
						const { index, displayValue, exportValue } = event.detail.insert;
						const selectChild = selectElement.children[index];
						const optionElement = document.createElement("option");
						optionElement.textContent = displayValue;
						optionElement.value = exportValue;
						if (selectChild) selectChild.before(optionElement);
						else selectElement.append(optionElement);
						storage.setValue(id, {
							value: getValue(true),
							items: getItems(event)
						});
						selectedValues = getValue(false);
					},
					items(event) {
						const { items } = event.detail;
						while (selectElement.length !== 0) selectElement.remove(0);
						for (const item of items) {
							const { displayValue, exportValue } = item;
							const optionElement = document.createElement("option");
							optionElement.textContent = displayValue;
							optionElement.value = exportValue;
							selectElement.append(optionElement);
						}
						if (selectElement.options.length > 0) selectElement.options[0].selected = true;
						storage.setValue(id, {
							value: getValue(true),
							items: getItems(event)
						});
						selectedValues = getValue(false);
					},
					indices(event) {
						const indices = new Set(event.detail.indices);
						for (const option of event.target.options) option.selected = indices.has(option.index);
						storage.setValue(id, { value: getValue(true) });
						selectedValues = getValue(false);
					},
					editable(event) {
						event.target.disabled = !event.detail.editable;
					}
				}, jsEvent);
			});
			selectElement.addEventListener("input", (event) => {
				const exportValue = getValue(true);
				const change = getValue(false);
				storage.setValue(id, { value: exportValue });
				event.preventDefault();
				this.linkService.eventBus?.dispatch("dispatcheventinsandbox", {
					source: this,
					detail: {
						id,
						name: "Keystroke",
						value: selectedValues,
						change,
						changeEx: exportValue,
						willCommit: false,
						commitKey: 1,
						keyDown: false
					}
				});
			});
			this._setEventListeners(selectElement, null, [
				["focus", "Focus"],
				["blur", "Blur"],
				["mousedown", "Mouse Down"],
				["mouseenter", "Mouse Enter"],
				["mouseleave", "Mouse Exit"],
				["mouseup", "Mouse Up"],
				["input", "Action"],
				["input", "Validate"]
			], (event) => event.target.value);
		} else selectElement.addEventListener("input", function(event) {
			storage.setValue(id, { value: getValue(true) });
		});
		if (this.data.combo) this._setTextStyle(selectElement);
		this._setBackgroundColor(selectElement);
		this._setDefaultPropertiesFromJS(selectElement);
		this.container.append(selectElement);
		return this.container;
	}
};
var PopupAnnotationElement = class extends AnnotationElement {
	constructor(parameters) {
		const { data, elements } = parameters;
		super(parameters, { isRenderable: AnnotationElement._hasPopupData(data) });
		this.elements = elements;
		this.popup = null;
	}
	render() {
		this.container.classList.add("popupAnnotation");
		const popup = this.popup = new PopupElement({
			container: this.container,
			color: this.data.color,
			titleObj: this.data.titleObj,
			modificationDate: this.data.modificationDate,
			contentsObj: this.data.contentsObj,
			richText: this.data.richText,
			rect: this.data.rect,
			parentRect: this.data.parentRect || null,
			parent: this.parent,
			elements: this.elements,
			open: this.data.open
		});
		const elementIds = [];
		for (const element of this.elements) {
			element.popup = popup;
			element.container.ariaHasPopup = "dialog";
			elementIds.push(element.data.id);
			element.addHighlightArea();
		}
		this.container.setAttribute("aria-controls", elementIds.map((id) => `${AnnotationPrefix}${id}`).join(","));
		return this.container;
	}
};
var PopupElement = class {
	#boundKeyDown = this.#keyDown.bind(this);
	#boundHide = this.#hide.bind(this);
	#boundShow = this.#show.bind(this);
	#boundToggle = this.#toggle.bind(this);
	#color = null;
	#container = null;
	#contentsObj = null;
	#dateObj = null;
	#elements = null;
	#parent = null;
	#parentRect = null;
	#pinned = false;
	#popup = null;
	#position = null;
	#rect = null;
	#richText = null;
	#titleObj = null;
	#updates = null;
	#wasVisible = false;
	constructor({ container, color, elements, titleObj, modificationDate, contentsObj, richText, parent, rect, parentRect, open }) {
		this.#container = container;
		this.#titleObj = titleObj;
		this.#contentsObj = contentsObj;
		this.#richText = richText;
		this.#parent = parent;
		this.#color = color;
		this.#rect = rect;
		this.#parentRect = parentRect;
		this.#elements = elements;
		this.#dateObj = PDFDateString$1.toDateObject(modificationDate);
		this.trigger = elements.flatMap((e) => e.getElementsToTriggerPopup());
		for (const element of this.trigger) {
			element.addEventListener("click", this.#boundToggle);
			element.addEventListener("mouseenter", this.#boundShow);
			element.addEventListener("mouseleave", this.#boundHide);
			element.classList.add("popupTriggerArea");
		}
		for (const element of elements) element.container?.addEventListener("keydown", this.#boundKeyDown);
		this.#container.hidden = true;
		if (open) this.#toggle();
	}
	render() {
		if (this.#popup) return;
		const popup = this.#popup = document.createElement("div");
		popup.className = "popup";
		if (this.#color) {
			const baseColor = popup.style.outlineColor = Util$1.makeHexColor(...this.#color);
			if (CSS.supports("background-color", "color-mix(in srgb, red 30%, white)")) popup.style.backgroundColor = `color-mix(in srgb, ${baseColor} 30%, white)`;
			else {
				const BACKGROUND_ENLIGHT = .7;
				popup.style.backgroundColor = Util$1.makeHexColor(...this.#color.map((c) => Math.floor(BACKGROUND_ENLIGHT * (255 - c) + c)));
			}
		}
		const header = document.createElement("span");
		header.className = "header";
		const title = document.createElement("h1");
		header.append(title);
		({dir: title.dir, str: title.textContent} = this.#titleObj);
		popup.append(header);
		if (this.#dateObj) {
			const modificationDate = document.createElement("span");
			modificationDate.classList.add("popupDate");
			modificationDate.setAttribute("data-l10n-id", "pdfjs-annotation-date-time-string");
			modificationDate.setAttribute("data-l10n-args", JSON.stringify({ dateObj: this.#dateObj.valueOf() }));
			header.append(modificationDate);
		}
		const html = this.#html;
		if (html) {
			XfaLayer$1.render({
				xfaHtml: html,
				intent: "richText",
				div: popup
			});
			popup.lastChild.classList.add("richText", "popupContent");
		} else {
			const contents = this._formatContents(this.#contentsObj);
			popup.append(contents);
		}
		this.#container.append(popup);
	}
	get #html() {
		const richText = this.#richText;
		const contentsObj = this.#contentsObj;
		if (richText?.str && (!contentsObj?.str || contentsObj.str === richText.str)) return this.#richText.html || null;
		return null;
	}
	get #fontSize() {
		return this.#html?.attributes?.style?.fontSize || 0;
	}
	get #fontColor() {
		return this.#html?.attributes?.style?.color || null;
	}
	#makePopupContent(text) {
		const popupLines = [];
		const popupContent = {
			str: text,
			html: {
				name: "div",
				attributes: { dir: "auto" },
				children: [{
					name: "p",
					children: popupLines
				}]
			}
		};
		const lineAttributes = { style: {
			color: this.#fontColor,
			fontSize: this.#fontSize ? `calc(${this.#fontSize}px * var(--scale-factor))` : ""
		} };
		for (const line of text.split("\n")) popupLines.push({
			name: "span",
			value: line,
			attributes: lineAttributes
		});
		return popupContent;
	}
	_formatContents({ str, dir }) {
		const p = document.createElement("p");
		p.classList.add("popupContent");
		p.dir = dir;
		const lines = str.split(/(?:\r\n?|\n)/);
		for (let i = 0, ii = lines.length; i < ii; ++i) {
			const line = lines[i];
			p.append(document.createTextNode(line));
			if (i < ii - 1) p.append(document.createElement("br"));
		}
		return p;
	}
	#keyDown(event) {
		if (event.altKey || event.shiftKey || event.ctrlKey || event.metaKey) return;
		if (event.key === "Enter" || event.key === "Escape" && this.#pinned) this.#toggle();
	}
	updateEdited({ rect, popupContent }) {
		this.#updates ||= {
			contentsObj: this.#contentsObj,
			richText: this.#richText
		};
		if (rect) this.#position = null;
		if (popupContent) {
			this.#richText = this.#makePopupContent(popupContent);
			this.#contentsObj = null;
		}
		this.#popup?.remove();
		this.#popup = null;
	}
	resetEdited() {
		if (!this.#updates) return;
		({contentsObj: this.#contentsObj, richText: this.#richText} = this.#updates);
		this.#updates = null;
		this.#popup?.remove();
		this.#popup = null;
		this.#position = null;
	}
	#setPosition() {
		if (this.#position !== null) return;
		const { page: { view }, viewport: { rawDims: { pageWidth, pageHeight, pageX, pageY } } } = this.#parent;
		let useParentRect = !!this.#parentRect;
		let rect = useParentRect ? this.#parentRect : this.#rect;
		for (const element of this.#elements) if (!rect || Util$1.intersect(element.data.rect, rect) !== null) {
			rect = element.data.rect;
			useParentRect = true;
			break;
		}
		const normalizedRect = Util$1.normalizeRect([
			rect[0],
			view[3] - rect[1] + view[1],
			rect[2],
			view[3] - rect[3] + view[1]
		]);
		const parentWidth = useParentRect ? rect[2] - rect[0] + 5 : 0;
		const popupLeft = normalizedRect[0] + parentWidth;
		const popupTop = normalizedRect[1];
		this.#position = [100 * (popupLeft - pageX) / pageWidth, 100 * (popupTop - pageY) / pageHeight];
		const { style } = this.#container;
		style.left = `${this.#position[0]}%`;
		style.top = `${this.#position[1]}%`;
	}
	#toggle() {
		this.#pinned = !this.#pinned;
		if (this.#pinned) {
			this.#show();
			this.#container.addEventListener("click", this.#boundToggle);
			this.#container.addEventListener("keydown", this.#boundKeyDown);
		} else {
			this.#hide();
			this.#container.removeEventListener("click", this.#boundToggle);
			this.#container.removeEventListener("keydown", this.#boundKeyDown);
		}
	}
	#show() {
		if (!this.#popup) this.render();
		if (!this.isVisible) {
			this.#setPosition();
			this.#container.hidden = false;
			this.#container.style.zIndex = parseInt(this.#container.style.zIndex) + 1e3;
		} else if (this.#pinned) this.#container.classList.add("focused");
	}
	#hide() {
		this.#container.classList.remove("focused");
		if (this.#pinned || !this.isVisible) return;
		this.#container.hidden = true;
		this.#container.style.zIndex = parseInt(this.#container.style.zIndex) - 1e3;
	}
	forceHide() {
		this.#wasVisible = this.isVisible;
		if (!this.#wasVisible) return;
		this.#container.hidden = true;
	}
	maybeShow() {
		if (!this.#wasVisible) return;
		if (!this.#popup) this.#show();
		this.#wasVisible = false;
		this.#container.hidden = false;
	}
	get isVisible() {
		return this.#container.hidden === false;
	}
};
var FreeTextAnnotationElement = class extends AnnotationElement {
	constructor(parameters) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: true
		});
		this.textContent = parameters.data.textContent;
		this.textPosition = parameters.data.textPosition;
		this.annotationEditorType = AnnotationEditorType$1.FREETEXT;
	}
	render() {
		this.container.classList.add("freeTextAnnotation");
		if (this.textContent) {
			const content = document.createElement("div");
			content.classList.add("annotationTextContent");
			content.setAttribute("role", "comment");
			for (const line of this.textContent) {
				const lineSpan = document.createElement("span");
				lineSpan.textContent = line;
				content.append(lineSpan);
			}
			this.container.append(content);
		}
		if (!this.data.popupRef && this.hasPopupData) this._createPopup();
		this._editOnDoubleClick();
		return this.container;
	}
};
var LineAnnotationElement = class extends AnnotationElement {
	#line = null;
	constructor(parameters) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: true
		});
	}
	render() {
		this.container.classList.add("lineAnnotation");
		const data = this.data;
		const { width, height } = getRectDims(data.rect);
		const svg = this.svgFactory.create(width, height, true);
		const line = this.#line = this.svgFactory.createElement("svg:line");
		line.setAttribute("x1", data.rect[2] - data.lineCoordinates[0]);
		line.setAttribute("y1", data.rect[3] - data.lineCoordinates[1]);
		line.setAttribute("x2", data.rect[2] - data.lineCoordinates[2]);
		line.setAttribute("y2", data.rect[3] - data.lineCoordinates[3]);
		line.setAttribute("stroke-width", data.borderStyle.width || 1);
		line.setAttribute("stroke", "transparent");
		line.setAttribute("fill", "transparent");
		svg.append(line);
		this.container.append(svg);
		if (!data.popupRef && this.hasPopupData) this._createPopup();
		return this.container;
	}
	getElementsToTriggerPopup() {
		return this.#line;
	}
	addHighlightArea() {
		this.container.classList.add("highlightArea");
	}
};
var SquareAnnotationElement = class extends AnnotationElement {
	#square = null;
	constructor(parameters) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: true
		});
	}
	render() {
		this.container.classList.add("squareAnnotation");
		const data = this.data;
		const { width, height } = getRectDims(data.rect);
		const svg = this.svgFactory.create(width, height, true);
		const borderWidth = data.borderStyle.width;
		const square = this.#square = this.svgFactory.createElement("svg:rect");
		square.setAttribute("x", borderWidth / 2);
		square.setAttribute("y", borderWidth / 2);
		square.setAttribute("width", width - borderWidth);
		square.setAttribute("height", height - borderWidth);
		square.setAttribute("stroke-width", borderWidth || 1);
		square.setAttribute("stroke", "transparent");
		square.setAttribute("fill", "transparent");
		svg.append(square);
		this.container.append(svg);
		if (!data.popupRef && this.hasPopupData) this._createPopup();
		return this.container;
	}
	getElementsToTriggerPopup() {
		return this.#square;
	}
	addHighlightArea() {
		this.container.classList.add("highlightArea");
	}
};
var CircleAnnotationElement = class extends AnnotationElement {
	#circle = null;
	constructor(parameters) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: true
		});
	}
	render() {
		this.container.classList.add("circleAnnotation");
		const data = this.data;
		const { width, height } = getRectDims(data.rect);
		const svg = this.svgFactory.create(width, height, true);
		const borderWidth = data.borderStyle.width;
		const circle = this.#circle = this.svgFactory.createElement("svg:ellipse");
		circle.setAttribute("cx", width / 2);
		circle.setAttribute("cy", height / 2);
		circle.setAttribute("rx", width / 2 - borderWidth / 2);
		circle.setAttribute("ry", height / 2 - borderWidth / 2);
		circle.setAttribute("stroke-width", borderWidth || 1);
		circle.setAttribute("stroke", "transparent");
		circle.setAttribute("fill", "transparent");
		svg.append(circle);
		this.container.append(svg);
		if (!data.popupRef && this.hasPopupData) this._createPopup();
		return this.container;
	}
	getElementsToTriggerPopup() {
		return this.#circle;
	}
	addHighlightArea() {
		this.container.classList.add("highlightArea");
	}
};
var PolylineAnnotationElement = class extends AnnotationElement {
	#polyline = null;
	constructor(parameters) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: true
		});
		this.containerClassName = "polylineAnnotation";
		this.svgElementName = "svg:polyline";
	}
	render() {
		this.container.classList.add(this.containerClassName);
		const { data: { rect, vertices, borderStyle, popupRef } } = this;
		if (!vertices) return this.container;
		const { width, height } = getRectDims(rect);
		const svg = this.svgFactory.create(width, height, true);
		let points = [];
		for (let i = 0, ii = vertices.length; i < ii; i += 2) {
			const x = vertices[i] - rect[0];
			const y = rect[3] - vertices[i + 1];
			points.push(`${x},${y}`);
		}
		points = points.join(" ");
		const polyline = this.#polyline = this.svgFactory.createElement(this.svgElementName);
		polyline.setAttribute("points", points);
		polyline.setAttribute("stroke-width", borderStyle.width || 1);
		polyline.setAttribute("stroke", "transparent");
		polyline.setAttribute("fill", "transparent");
		svg.append(polyline);
		this.container.append(svg);
		if (!popupRef && this.hasPopupData) this._createPopup();
		return this.container;
	}
	getElementsToTriggerPopup() {
		return this.#polyline;
	}
	addHighlightArea() {
		this.container.classList.add("highlightArea");
	}
};
var PolygonAnnotationElement = class extends PolylineAnnotationElement {
	constructor(parameters) {
		super(parameters);
		this.containerClassName = "polygonAnnotation";
		this.svgElementName = "svg:polygon";
	}
};
var CaretAnnotationElement = class extends AnnotationElement {
	constructor(parameters) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: true
		});
	}
	render() {
		this.container.classList.add("caretAnnotation");
		if (!this.data.popupRef && this.hasPopupData) this._createPopup();
		return this.container;
	}
};
var InkAnnotationElement = class extends AnnotationElement {
	#polylinesGroupElement = null;
	#polylines = [];
	constructor(parameters) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: true
		});
		this.containerClassName = "inkAnnotation";
		this.svgElementName = "svg:polyline";
		this.annotationEditorType = this.data.it === "InkHighlight" ? AnnotationEditorType$1.HIGHLIGHT : AnnotationEditorType$1.INK;
	}
	#getTransform(rotation, rect) {
		switch (rotation) {
			case 90: return {
				transform: `rotate(90) translate(${-rect[0]},${rect[1]}) scale(1,-1)`,
				width: rect[3] - rect[1],
				height: rect[2] - rect[0]
			};
			case 180: return {
				transform: `rotate(180) translate(${-rect[2]},${rect[1]}) scale(1,-1)`,
				width: rect[2] - rect[0],
				height: rect[3] - rect[1]
			};
			case 270: return {
				transform: `rotate(270) translate(${-rect[2]},${rect[3]}) scale(1,-1)`,
				width: rect[3] - rect[1],
				height: rect[2] - rect[0]
			};
			default: return {
				transform: `translate(${-rect[0]},${rect[3]}) scale(1,-1)`,
				width: rect[2] - rect[0],
				height: rect[3] - rect[1]
			};
		}
	}
	render() {
		this.container.classList.add(this.containerClassName);
		const { data: { rect, rotation, inkLists, borderStyle, popupRef } } = this;
		const { transform, width, height } = this.#getTransform(rotation, rect);
		const svg = this.svgFactory.create(width, height, true);
		const g = this.#polylinesGroupElement = this.svgFactory.createElement("svg:g");
		svg.append(g);
		g.setAttribute("stroke-width", borderStyle.width || 1);
		g.setAttribute("stroke-linecap", "round");
		g.setAttribute("stroke-linejoin", "round");
		g.setAttribute("stroke-miterlimit", 10);
		g.setAttribute("stroke", "transparent");
		g.setAttribute("fill", "transparent");
		g.setAttribute("transform", transform);
		for (let i = 0, ii = inkLists.length; i < ii; i++) {
			const polyline = this.svgFactory.createElement(this.svgElementName);
			this.#polylines.push(polyline);
			polyline.setAttribute("points", inkLists[i].join(","));
			g.append(polyline);
		}
		if (!popupRef && this.hasPopupData) this._createPopup();
		this.container.append(svg);
		this._editOnDoubleClick();
		return this.container;
	}
	updateEdited(params) {
		super.updateEdited(params);
		const { thickness, points, rect } = params;
		const g = this.#polylinesGroupElement;
		if (thickness >= 0) g.setAttribute("stroke-width", thickness || 1);
		if (points) for (let i = 0, ii = this.#polylines.length; i < ii; i++) this.#polylines[i].setAttribute("points", points[i].join(","));
		if (rect) {
			const { transform, width, height } = this.#getTransform(this.data.rotation, rect);
			g.parentElement.setAttribute("viewBox", `0 0 ${width} ${height}`);
			g.setAttribute("transform", transform);
		}
	}
	getElementsToTriggerPopup() {
		return this.#polylines;
	}
	addHighlightArea() {
		this.container.classList.add("highlightArea");
	}
};
var HighlightAnnotationElement = class extends AnnotationElement {
	constructor(parameters) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: true,
			createQuadrilaterals: true
		});
		this.annotationEditorType = AnnotationEditorType$1.HIGHLIGHT;
	}
	render() {
		if (!this.data.popupRef && this.hasPopupData) this._createPopup();
		this.container.classList.add("highlightAnnotation");
		this._editOnDoubleClick();
		return this.container;
	}
};
var UnderlineAnnotationElement = class extends AnnotationElement {
	constructor(parameters) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: true,
			createQuadrilaterals: true
		});
	}
	render() {
		if (!this.data.popupRef && this.hasPopupData) this._createPopup();
		this.container.classList.add("underlineAnnotation");
		return this.container;
	}
};
var SquigglyAnnotationElement = class extends AnnotationElement {
	constructor(parameters) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: true,
			createQuadrilaterals: true
		});
	}
	render() {
		if (!this.data.popupRef && this.hasPopupData) this._createPopup();
		this.container.classList.add("squigglyAnnotation");
		return this.container;
	}
};
var StrikeOutAnnotationElement = class extends AnnotationElement {
	constructor(parameters) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: true,
			createQuadrilaterals: true
		});
	}
	render() {
		if (!this.data.popupRef && this.hasPopupData) this._createPopup();
		this.container.classList.add("strikeoutAnnotation");
		return this.container;
	}
};
var StampAnnotationElement = class extends AnnotationElement {
	constructor(parameters) {
		super(parameters, {
			isRenderable: true,
			ignoreBorder: true
		});
		this.annotationEditorType = AnnotationEditorType$1.STAMP;
	}
	render() {
		this.container.classList.add("stampAnnotation");
		this.container.setAttribute("role", "img");
		if (!this.data.popupRef && this.hasPopupData) this._createPopup();
		this._editOnDoubleClick();
		return this.container;
	}
};
var FileAttachmentAnnotationElement = class extends AnnotationElement {
	#trigger = null;
	constructor(parameters) {
		super(parameters, { isRenderable: true });
		const { file } = this.data;
		this.filename = file.filename;
		this.content = file.content;
		this.linkService.eventBus?.dispatch("fileattachmentannotation", {
			source: this,
			...file
		});
	}
	render() {
		this.container.classList.add("fileAttachmentAnnotation");
		const { container, data } = this;
		let trigger;
		if (data.hasAppearance || data.fillAlpha === 0) trigger = document.createElement("div");
		else {
			trigger = document.createElement("img");
			trigger.src = `${this.imageResourcesPath}annotation-${/paperclip/i.test(data.name) ? "paperclip" : "pushpin"}.svg`;
			if (data.fillAlpha && data.fillAlpha < 1) trigger.style = `filter: opacity(${Math.round(data.fillAlpha * 100)}%);`;
		}
		trigger.addEventListener("dblclick", this.#download.bind(this));
		this.#trigger = trigger;
		const { isMac } = util_FeatureTest.platform;
		container.addEventListener("keydown", (evt) => {
			if (evt.key === "Enter" && (isMac ? evt.metaKey : evt.ctrlKey)) this.#download();
		});
		if (!data.popupRef && this.hasPopupData) this._createPopup();
		else trigger.classList.add("popupTriggerArea");
		container.append(trigger);
		return container;
	}
	getElementsToTriggerPopup() {
		return this.#trigger;
	}
	addHighlightArea() {
		this.container.classList.add("highlightArea");
	}
	#download() {
		this.downloadManager?.openOrDownloadData(this.content, this.filename);
	}
};
var AnnotationLayer$1 = class {
	#accessibilityManager = null;
	#annotationCanvasMap = null;
	#editableAnnotations = /* @__PURE__ */ new Map();
	#structTreeLayer = null;
	constructor({ div, accessibilityManager, annotationCanvasMap, annotationEditorUIManager, page, viewport, structTreeLayer }) {
		this.div = div;
		this.#accessibilityManager = accessibilityManager;
		this.#annotationCanvasMap = annotationCanvasMap;
		this.#structTreeLayer = structTreeLayer || null;
		this.page = page;
		this.viewport = viewport;
		this.zIndex = 0;
		this._annotationEditorUIManager = annotationEditorUIManager;
	}
	hasEditableAnnotations() {
		return this.#editableAnnotations.size > 0;
	}
	async #appendElement(element, id) {
		const contentElement = element.firstChild || element;
		const annotationId = contentElement.id = `${AnnotationPrefix}${id}`;
		const ariaAttributes = await this.#structTreeLayer?.getAriaAttributes(annotationId);
		if (ariaAttributes) for (const [key, value] of ariaAttributes) contentElement.setAttribute(key, value);
		this.div.append(element);
		this.#accessibilityManager?.moveElementInDOM(this.div, element, contentElement, false);
	}
	async render(params) {
		const { annotations } = params;
		const layer = this.div;
		setLayerDimensions$1(layer, this.viewport);
		const popupToElements = /* @__PURE__ */ new Map();
		const elementParams = {
			data: null,
			layer,
			linkService: params.linkService,
			downloadManager: params.downloadManager,
			imageResourcesPath: params.imageResourcesPath || "",
			renderForms: params.renderForms !== false,
			svgFactory: new DOMSVGFactory$1(),
			annotationStorage: params.annotationStorage || new AnnotationStorage(),
			enableScripting: params.enableScripting === true,
			hasJSActions: params.hasJSActions,
			fieldObjects: params.fieldObjects,
			parent: this,
			elements: null
		};
		for (const data of annotations) {
			if (data.noHTML) continue;
			const isPopupAnnotation = data.annotationType === AnnotationType.POPUP;
			if (!isPopupAnnotation) {
				const { width, height } = getRectDims(data.rect);
				if (width <= 0 || height <= 0) continue;
			} else {
				const elements = popupToElements.get(data.id);
				if (!elements) continue;
				elementParams.elements = elements;
			}
			elementParams.data = data;
			const element = AnnotationElementFactory.create(elementParams);
			if (!element.isRenderable) continue;
			if (!isPopupAnnotation && data.popupRef) {
				const elements = popupToElements.get(data.popupRef);
				if (!elements) popupToElements.set(data.popupRef, [element]);
				else elements.push(element);
			}
			const rendered = element.render();
			if (data.hidden) rendered.style.visibility = "hidden";
			await this.#appendElement(rendered, data.id);
			if (element._isEditable) {
				this.#editableAnnotations.set(element.data.id, element);
				this._annotationEditorUIManager?.renderAnnotationElement(element);
			}
		}
		this.#setAnnotationCanvasMap();
	}
	update({ viewport }) {
		const layer = this.div;
		this.viewport = viewport;
		setLayerDimensions$1(layer, { rotation: viewport.rotation });
		this.#setAnnotationCanvasMap();
		layer.hidden = false;
	}
	#setAnnotationCanvasMap() {
		if (!this.#annotationCanvasMap) return;
		const layer = this.div;
		for (const [id, canvas] of this.#annotationCanvasMap) {
			const element = layer.querySelector(`[data-annotation-id="${id}"]`);
			if (!element) continue;
			canvas.className = "annotationContent";
			const { firstChild } = element;
			if (!firstChild) element.append(canvas);
			else if (firstChild.nodeName === "CANVAS") firstChild.replaceWith(canvas);
			else if (!firstChild.classList.contains("annotationContent")) firstChild.before(canvas);
			else firstChild.after(canvas);
		}
		this.#annotationCanvasMap.clear();
	}
	getEditableAnnotations() {
		return Array.from(this.#editableAnnotations.values());
	}
	getEditableAnnotation(id) {
		return this.#editableAnnotations.get(id);
	}
};
var EOL_PATTERN = /\r\n?|\n/g;
var FreeTextEditor = class FreeTextEditor extends AnnotationEditor {
	#color;
	#content = "";
	#editorDivId = `${this.id}-editor`;
	#editModeAC = null;
	#fontSize;
	static _freeTextDefaultContent = "";
	static _internalPadding = 0;
	static _defaultColor = null;
	static _defaultFontSize = 10;
	static get _keyboardManager() {
		const proto = FreeTextEditor.prototype;
		const arrowChecker = (self) => self.isEmpty();
		const small = AnnotationEditorUIManager$1.TRANSLATE_SMALL;
		const big = AnnotationEditorUIManager$1.TRANSLATE_BIG;
		return shadow$1(this, "_keyboardManager", new KeyboardManager([
			[
				[
					"ctrl+s",
					"mac+meta+s",
					"ctrl+p",
					"mac+meta+p"
				],
				proto.commitOrRemove,
				{ bubbles: true }
			],
			[[
				"ctrl+Enter",
				"mac+meta+Enter",
				"Escape",
				"mac+Escape"
			], proto.commitOrRemove],
			[
				["ArrowLeft", "mac+ArrowLeft"],
				proto._translateEmpty,
				{
					args: [-small, 0],
					checker: arrowChecker
				}
			],
			[
				["ctrl+ArrowLeft", "mac+shift+ArrowLeft"],
				proto._translateEmpty,
				{
					args: [-big, 0],
					checker: arrowChecker
				}
			],
			[
				["ArrowRight", "mac+ArrowRight"],
				proto._translateEmpty,
				{
					args: [small, 0],
					checker: arrowChecker
				}
			],
			[
				["ctrl+ArrowRight", "mac+shift+ArrowRight"],
				proto._translateEmpty,
				{
					args: [big, 0],
					checker: arrowChecker
				}
			],
			[
				["ArrowUp", "mac+ArrowUp"],
				proto._translateEmpty,
				{
					args: [0, -small],
					checker: arrowChecker
				}
			],
			[
				["ctrl+ArrowUp", "mac+shift+ArrowUp"],
				proto._translateEmpty,
				{
					args: [0, -big],
					checker: arrowChecker
				}
			],
			[
				["ArrowDown", "mac+ArrowDown"],
				proto._translateEmpty,
				{
					args: [0, small],
					checker: arrowChecker
				}
			],
			[
				["ctrl+ArrowDown", "mac+shift+ArrowDown"],
				proto._translateEmpty,
				{
					args: [0, big],
					checker: arrowChecker
				}
			]
		]));
	}
	static _type = "freetext";
	static _editorType = AnnotationEditorType$1.FREETEXT;
	constructor(params) {
		super({
			...params,
			name: "freeTextEditor"
		});
		this.#color = params.color || FreeTextEditor._defaultColor || AnnotationEditor._defaultLineColor;
		this.#fontSize = params.fontSize || FreeTextEditor._defaultFontSize;
	}
	static initialize(l10n, uiManager) {
		AnnotationEditor.initialize(l10n, uiManager);
		const style = getComputedStyle(document.documentElement);
		this._internalPadding = parseFloat(style.getPropertyValue("--freetext-padding"));
	}
	static updateDefaultParams(type, value) {
		switch (type) {
			case AnnotationEditorParamsType$1.FREETEXT_SIZE:
				FreeTextEditor._defaultFontSize = value;
				break;
			case AnnotationEditorParamsType$1.FREETEXT_COLOR: FreeTextEditor._defaultColor = value;
		}
	}
	updateParams(type, value) {
		switch (type) {
			case AnnotationEditorParamsType$1.FREETEXT_SIZE:
				this.#updateFontSize(value);
				break;
			case AnnotationEditorParamsType$1.FREETEXT_COLOR: this.#updateColor(value);
		}
	}
	static get defaultPropertiesToUpdate() {
		return [[AnnotationEditorParamsType$1.FREETEXT_SIZE, FreeTextEditor._defaultFontSize], [AnnotationEditorParamsType$1.FREETEXT_COLOR, FreeTextEditor._defaultColor || AnnotationEditor._defaultLineColor]];
	}
	get propertiesToUpdate() {
		return [[AnnotationEditorParamsType$1.FREETEXT_SIZE, this.#fontSize], [AnnotationEditorParamsType$1.FREETEXT_COLOR, this.#color]];
	}
	#updateFontSize(fontSize) {
		const setFontsize = (size) => {
			this.editorDiv.style.fontSize = `calc(${size}px * var(--scale-factor))`;
			this.translate(0, -(size - this.#fontSize) * this.parentScale);
			this.#fontSize = size;
			this.#setEditorDimensions();
		};
		const savedFontsize = this.#fontSize;
		this.addCommands({
			cmd: setFontsize.bind(this, fontSize),
			undo: setFontsize.bind(this, savedFontsize),
			post: this._uiManager.updateUI.bind(this._uiManager, this),
			mustExec: true,
			type: AnnotationEditorParamsType$1.FREETEXT_SIZE,
			overwriteIfSameType: true,
			keepUndo: true
		});
	}
	#updateColor(color) {
		const setColor = (col) => {
			this.#color = this.editorDiv.style.color = col;
		};
		const savedColor = this.#color;
		this.addCommands({
			cmd: setColor.bind(this, color),
			undo: setColor.bind(this, savedColor),
			post: this._uiManager.updateUI.bind(this._uiManager, this),
			mustExec: true,
			type: AnnotationEditorParamsType$1.FREETEXT_COLOR,
			overwriteIfSameType: true,
			keepUndo: true
		});
	}
	_translateEmpty(x, y) {
		this._uiManager.translateSelectedEditors(x, y, true);
	}
	getInitialTranslation() {
		const scale = this.parentScale;
		return [-FreeTextEditor._internalPadding * scale, -(FreeTextEditor._internalPadding + this.#fontSize) * scale];
	}
	rebuild() {
		if (!this.parent) return;
		super.rebuild();
		if (this.div === null) return;
		if (!this.isAttachedToDOM) this.parent.add(this);
	}
	enableEditMode() {
		if (this.isInEditMode()) return;
		this.parent.setEditingState(false);
		this.parent.updateToolbar(AnnotationEditorType$1.FREETEXT);
		super.enableEditMode();
		this.overlayDiv.classList.remove("enabled");
		this.editorDiv.contentEditable = true;
		this._isDraggable = false;
		this.div.removeAttribute("aria-activedescendant");
		this.#editModeAC = new AbortController();
		const signal = this._uiManager.combinedSignal(this.#editModeAC);
		this.editorDiv.addEventListener("keydown", this.editorDivKeydown.bind(this), { signal });
		this.editorDiv.addEventListener("focus", this.editorDivFocus.bind(this), { signal });
		this.editorDiv.addEventListener("blur", this.editorDivBlur.bind(this), { signal });
		this.editorDiv.addEventListener("input", this.editorDivInput.bind(this), { signal });
		this.editorDiv.addEventListener("paste", this.editorDivPaste.bind(this), { signal });
	}
	disableEditMode() {
		if (!this.isInEditMode()) return;
		this.parent.setEditingState(true);
		super.disableEditMode();
		this.overlayDiv.classList.add("enabled");
		this.editorDiv.contentEditable = false;
		this.div.setAttribute("aria-activedescendant", this.#editorDivId);
		this._isDraggable = true;
		this.#editModeAC?.abort();
		this.#editModeAC = null;
		this.div.focus({ preventScroll: true });
		this.isEditing = false;
		this.parent.div.classList.add("freetextEditing");
	}
	focusin(event) {
		if (!this._focusEventsAllowed) return;
		super.focusin(event);
		if (event.target !== this.editorDiv) this.editorDiv.focus();
	}
	onceAdded(focus) {
		if (this.width) return;
		this.enableEditMode();
		if (focus) this.editorDiv.focus();
		if (this._initialOptions?.isCentered) this.center();
		this._initialOptions = null;
	}
	isEmpty() {
		return !this.editorDiv || this.editorDiv.innerText.trim() === "";
	}
	remove() {
		this.isEditing = false;
		if (this.parent) {
			this.parent.setEditingState(true);
			this.parent.div.classList.add("freetextEditing");
		}
		super.remove();
	}
	#extractText() {
		const buffer = [];
		this.editorDiv.normalize();
		let prevChild = null;
		for (const child of this.editorDiv.childNodes) {
			if (prevChild?.nodeType === Node.TEXT_NODE && child.nodeName === "BR") continue;
			buffer.push(FreeTextEditor.#getNodeContent(child));
			prevChild = child;
		}
		return buffer.join("\n");
	}
	#setEditorDimensions() {
		const [parentWidth, parentHeight] = this.parentDimensions;
		let rect;
		if (this.isAttachedToDOM) rect = this.div.getBoundingClientRect();
		else {
			const { currentLayer, div } = this;
			const savedDisplay = div.style.display;
			const savedVisibility = div.classList.contains("hidden");
			div.classList.remove("hidden");
			div.style.display = "hidden";
			currentLayer.div.append(this.div);
			rect = div.getBoundingClientRect();
			div.remove();
			div.style.display = savedDisplay;
			div.classList.toggle("hidden", savedVisibility);
		}
		if (this.rotation % 180 === this.parentRotation % 180) {
			this.width = rect.width / parentWidth;
			this.height = rect.height / parentHeight;
		} else {
			this.width = rect.height / parentWidth;
			this.height = rect.width / parentHeight;
		}
		this.fixAndSetPosition();
	}
	commit() {
		if (!this.isInEditMode()) return;
		super.commit();
		this.disableEditMode();
		const savedText = this.#content;
		const newText = this.#content = this.#extractText().trimEnd();
		if (savedText === newText) return;
		const setText = (text) => {
			this.#content = text;
			if (!text) {
				this.remove();
				return;
			}
			this.#setContent();
			this._uiManager.rebuild(this);
			this.#setEditorDimensions();
		};
		this.addCommands({
			cmd: () => {
				setText(newText);
			},
			undo: () => {
				setText(savedText);
			},
			mustExec: false
		});
		this.#setEditorDimensions();
	}
	shouldGetKeyboardEvents() {
		return this.isInEditMode();
	}
	enterInEditMode() {
		this.enableEditMode();
		this.editorDiv.focus();
	}
	dblclick(event) {
		this.enterInEditMode();
	}
	keydown(event) {
		if (event.target === this.div && event.key === "Enter") {
			this.enterInEditMode();
			event.preventDefault();
		}
	}
	editorDivKeydown(event) {
		FreeTextEditor._keyboardManager.exec(this, event);
	}
	editorDivFocus(event) {
		this.isEditing = true;
	}
	editorDivBlur(event) {
		this.isEditing = false;
	}
	editorDivInput(event) {
		this.parent.div.classList.toggle("freetextEditing", this.isEmpty());
	}
	disableEditing() {
		this.editorDiv.setAttribute("role", "comment");
		this.editorDiv.removeAttribute("aria-multiline");
	}
	enableEditing() {
		this.editorDiv.setAttribute("role", "textbox");
		this.editorDiv.setAttribute("aria-multiline", true);
	}
	render() {
		if (this.div) return this.div;
		let baseX, baseY;
		if (this.width) {
			baseX = this.x;
			baseY = this.y;
		}
		super.render();
		this.editorDiv = document.createElement("div");
		this.editorDiv.className = "internal";
		this.editorDiv.setAttribute("id", this.#editorDivId);
		this.editorDiv.setAttribute("data-l10n-id", "pdfjs-free-text2");
		this.editorDiv.setAttribute("data-l10n-attrs", "default-content");
		this.enableEditing();
		this.editorDiv.contentEditable = true;
		const { style } = this.editorDiv;
		style.fontSize = `calc(${this.#fontSize}px * var(--scale-factor))`;
		style.color = this.#color;
		this.div.append(this.editorDiv);
		this.overlayDiv = document.createElement("div");
		this.overlayDiv.classList.add("overlay", "enabled");
		this.div.append(this.overlayDiv);
		bindEvents(this, this.div, ["dblclick", "keydown"]);
		if (this.width) {
			const [parentWidth, parentHeight] = this.parentDimensions;
			if (this.annotationElementId) {
				const { position } = this._initialData;
				let [tx, ty] = this.getInitialTranslation();
				[tx, ty] = this.pageTranslationToScreen(tx, ty);
				const [pageWidth, pageHeight] = this.pageDimensions;
				const [pageX, pageY] = this.pageTranslation;
				let posX, posY;
				switch (this.rotation) {
					case 0:
						posX = baseX + (position[0] - pageX) / pageWidth;
						posY = baseY + this.height - (position[1] - pageY) / pageHeight;
						break;
					case 90:
						posX = baseX + (position[0] - pageX) / pageWidth;
						posY = baseY - (position[1] - pageY) / pageHeight;
						[tx, ty] = [ty, -tx];
						break;
					case 180:
						posX = baseX - this.width + (position[0] - pageX) / pageWidth;
						posY = baseY - (position[1] - pageY) / pageHeight;
						[tx, ty] = [-tx, -ty];
						break;
					case 270:
						posX = baseX + (position[0] - pageX - this.height * pageHeight) / pageWidth;
						posY = baseY + (position[1] - pageY - this.width * pageWidth) / pageHeight;
						[tx, ty] = [-ty, tx];
				}
				this.setAt(posX * parentWidth, posY * parentHeight, tx, ty);
			} else this.setAt(baseX * parentWidth, baseY * parentHeight, this.width * parentWidth, this.height * parentHeight);
			this.#setContent();
			this._isDraggable = true;
			this.editorDiv.contentEditable = false;
		} else {
			this._isDraggable = false;
			this.editorDiv.contentEditable = true;
		}
		return this.div;
	}
	static #getNodeContent(node) {
		return (node.nodeType === Node.TEXT_NODE ? node.nodeValue : node.innerText).replaceAll(EOL_PATTERN, "");
	}
	editorDivPaste(event) {
		const clipboardData = event.clipboardData || window.clipboardData;
		const { types } = clipboardData;
		if (types.length === 1 && types[0] === "text/plain") return;
		event.preventDefault();
		const paste = FreeTextEditor.#deserializeContent(clipboardData.getData("text") || "").replaceAll(EOL_PATTERN, "\n");
		if (!paste) return;
		const selection = window.getSelection();
		if (!selection.rangeCount) return;
		this.editorDiv.normalize();
		selection.deleteFromDocument();
		const range = selection.getRangeAt(0);
		if (!paste.includes("\n")) {
			range.insertNode(document.createTextNode(paste));
			this.editorDiv.normalize();
			selection.collapseToStart();
			return;
		}
		const { startContainer, startOffset } = range;
		const bufferBefore = [];
		const bufferAfter = [];
		if (startContainer.nodeType === Node.TEXT_NODE) {
			const parent = startContainer.parentElement;
			bufferAfter.push(startContainer.nodeValue.slice(startOffset).replaceAll(EOL_PATTERN, ""));
			if (parent !== this.editorDiv) {
				let buffer = bufferBefore;
				for (const child of this.editorDiv.childNodes) {
					if (child === parent) {
						buffer = bufferAfter;
						continue;
					}
					buffer.push(FreeTextEditor.#getNodeContent(child));
				}
			}
			bufferBefore.push(startContainer.nodeValue.slice(0, startOffset).replaceAll(EOL_PATTERN, ""));
		} else if (startContainer === this.editorDiv) {
			let buffer = bufferBefore;
			let i = 0;
			for (const child of this.editorDiv.childNodes) {
				if (i++ === startOffset) buffer = bufferAfter;
				buffer.push(FreeTextEditor.#getNodeContent(child));
			}
		}
		this.#content = `${bufferBefore.join("\n")}${paste}${bufferAfter.join("\n")}`;
		this.#setContent();
		const newRange = new Range();
		let beforeLength = bufferBefore.reduce((acc, line) => acc + line.length, 0);
		for (const { firstChild } of this.editorDiv.childNodes) if (firstChild.nodeType === Node.TEXT_NODE) {
			const length = firstChild.nodeValue.length;
			if (beforeLength <= length) {
				newRange.setStart(firstChild, beforeLength);
				newRange.setEnd(firstChild, beforeLength);
				break;
			}
			beforeLength -= length;
		}
		selection.removeAllRanges();
		selection.addRange(newRange);
	}
	#setContent() {
		this.editorDiv.replaceChildren();
		if (!this.#content) return;
		for (const line of this.#content.split("\n")) {
			const div = document.createElement("div");
			div.append(line ? document.createTextNode(line) : document.createElement("br"));
			this.editorDiv.append(div);
		}
	}
	#serializeContent() {
		return this.#content.replaceAll("\xA0", " ");
	}
	static #deserializeContent(content) {
		return content.replaceAll(" ", "\xA0");
	}
	get contentDiv() {
		return this.editorDiv;
	}
	static async deserialize(data, parent, uiManager) {
		let initialData = null;
		if (data instanceof FreeTextAnnotationElement) {
			const { data: { defaultAppearanceData: { fontSize, fontColor }, rect, rotation, id, popupRef }, textContent, textPosition, parent: { page: { pageNumber } } } = data;
			if (!textContent || textContent.length === 0) return null;
			initialData = data = {
				annotationType: AnnotationEditorType$1.FREETEXT,
				color: Array.from(fontColor),
				fontSize,
				value: textContent.join("\n"),
				position: textPosition,
				pageIndex: pageNumber - 1,
				rect: rect.slice(0),
				rotation,
				id,
				deleted: false,
				popupRef
			};
		}
		const editor = await super.deserialize(data, parent, uiManager);
		editor.#fontSize = data.fontSize;
		editor.#color = Util$1.makeHexColor(...data.color);
		editor.#content = FreeTextEditor.#deserializeContent(data.value);
		editor.annotationElementId = data.id || null;
		editor._initialData = initialData;
		return editor;
	}
	serialize(isForCopying = false) {
		if (this.isEmpty()) return null;
		if (this.deleted) return this.serializeDeleted();
		const padding = FreeTextEditor._internalPadding * this.parentScale;
		const rect = this.getRect(padding, padding);
		const color = AnnotationEditor._colorManager.convert(this.isAttachedToDOM ? getComputedStyle(this.editorDiv).color : this.#color);
		const serialized = {
			annotationType: AnnotationEditorType$1.FREETEXT,
			color,
			fontSize: this.#fontSize,
			value: this.#serializeContent(),
			pageIndex: this.pageIndex,
			rect,
			rotation: this.rotation,
			structTreeParentId: this._structTreeParentId
		};
		if (isForCopying) return serialized;
		if (this.annotationElementId && !this.#hasElementChanged(serialized)) return null;
		serialized.id = this.annotationElementId;
		return serialized;
	}
	#hasElementChanged(serialized) {
		const { value, fontSize, color, pageIndex } = this._initialData;
		return this._hasBeenMoved || serialized.value !== value || serialized.fontSize !== fontSize || serialized.color.some((c, i) => c !== color[i]) || serialized.pageIndex !== pageIndex;
	}
	renderAnnotationElement(annotation) {
		const content = super.renderAnnotationElement(annotation);
		if (this.deleted) return content;
		const { style } = content;
		style.fontSize = `calc(${this.#fontSize}px * var(--scale-factor))`;
		style.color = this.#color;
		content.replaceChildren();
		for (const line of this.#content.split("\n")) {
			const div = document.createElement("div");
			div.append(line ? document.createTextNode(line) : document.createElement("br"));
			content.append(div);
		}
		const padding = FreeTextEditor._internalPadding * this.parentScale;
		annotation.updateEdited({
			rect: this.getRect(padding, padding),
			popupContent: this.#content
		});
		return content;
	}
	resetAnnotationElement(annotation) {
		super.resetAnnotationElement(annotation);
		annotation.resetEdited();
	}
};
var Outline = class {
	static PRECISION = 1e-4;
	toSVGPath() {
		unreachable("Abstract method `toSVGPath` must be implemented.");
	}
	get box() {
		unreachable("Abstract getter `box` must be implemented.");
	}
	serialize(_bbox, _rotation) {
		unreachable("Abstract method `serialize` must be implemented.");
	}
	static _rescale(src, tx, ty, sx, sy, dest) {
		dest ||= new Float32Array(src.length);
		for (let i = 0, ii = src.length; i < ii; i += 2) {
			dest[i] = tx + src[i] * sx;
			dest[i + 1] = ty + src[i + 1] * sy;
		}
		return dest;
	}
	static _rescaleAndSwap(src, tx, ty, sx, sy, dest) {
		dest ||= new Float32Array(src.length);
		for (let i = 0, ii = src.length; i < ii; i += 2) {
			dest[i] = tx + src[i + 1] * sx;
			dest[i + 1] = ty + src[i] * sy;
		}
		return dest;
	}
	static _translate(src, tx, ty, dest) {
		dest ||= new Float32Array(src.length);
		for (let i = 0, ii = src.length; i < ii; i += 2) {
			dest[i] = tx + src[i];
			dest[i + 1] = ty + src[i + 1];
		}
		return dest;
	}
	static svgRound(x) {
		return Math.round(x * 1e4);
	}
	static _normalizePoint(x, y, parentWidth, parentHeight, rotation) {
		switch (rotation) {
			case 90: return [1 - y / parentWidth, x / parentHeight];
			case 180: return [1 - x / parentWidth, 1 - y / parentHeight];
			case 270: return [y / parentWidth, 1 - x / parentHeight];
			default: return [x / parentWidth, y / parentHeight];
		}
	}
	static _normalizePagePoint(x, y, rotation) {
		switch (rotation) {
			case 90: return [1 - y, x];
			case 180: return [1 - x, 1 - y];
			case 270: return [y, 1 - x];
			default: return [x, y];
		}
	}
	static createBezierPoints(x1, y1, x2, y2, x3, y3) {
		return [
			(x1 + 5 * x2) / 6,
			(y1 + 5 * y2) / 6,
			(5 * x2 + x3) / 6,
			(5 * y2 + y3) / 6,
			(x2 + x3) / 2,
			(y2 + y3) / 2
		];
	}
};
var FreeDrawOutliner = class FreeDrawOutliner {
	#box;
	#bottom = [];
	#innerMargin;
	#isLTR;
	#top = [];
	#last = /* @__PURE__ */ new Float32Array(18);
	#lastX;
	#lastY;
	#min;
	#min_dist;
	#scaleFactor;
	#thickness;
	#points = [];
	static #MIN_DIST = 8;
	static #MIN_DIFF = 2;
	static #MIN = FreeDrawOutliner.#MIN_DIST + FreeDrawOutliner.#MIN_DIFF;
	constructor({ x, y }, box, scaleFactor, thickness, isLTR, innerMargin = 0) {
		this.#box = box;
		this.#thickness = thickness * scaleFactor;
		this.#isLTR = isLTR;
		this.#last.set([
			NaN,
			NaN,
			NaN,
			NaN,
			x,
			y
		], 6);
		this.#innerMargin = innerMargin;
		this.#min_dist = FreeDrawOutliner.#MIN_DIST * scaleFactor;
		this.#min = FreeDrawOutliner.#MIN * scaleFactor;
		this.#scaleFactor = scaleFactor;
		this.#points.push(x, y);
	}
	isEmpty() {
		return isNaN(this.#last[8]);
	}
	#getLastCoords() {
		const lastTop = this.#last.subarray(4, 6);
		const lastBottom = this.#last.subarray(16, 18);
		const [x, y, width, height] = this.#box;
		return [
			(this.#lastX + (lastTop[0] - lastBottom[0]) / 2 - x) / width,
			(this.#lastY + (lastTop[1] - lastBottom[1]) / 2 - y) / height,
			(this.#lastX + (lastBottom[0] - lastTop[0]) / 2 - x) / width,
			(this.#lastY + (lastBottom[1] - lastTop[1]) / 2 - y) / height
		];
	}
	add({ x, y }) {
		this.#lastX = x;
		this.#lastY = y;
		const [layerX, layerY, layerWidth, layerHeight] = this.#box;
		let [x1, y1, x2, y2] = this.#last.subarray(8, 12);
		const diffX = x - x2;
		const diffY = y - y2;
		const d = Math.hypot(diffX, diffY);
		if (d < this.#min) return false;
		const diffD = d - this.#min_dist;
		const K = diffD / d;
		const shiftX = K * diffX;
		const shiftY = K * diffY;
		let x0 = x1;
		let y0 = y1;
		x1 = x2;
		y1 = y2;
		x2 += shiftX;
		y2 += shiftY;
		this.#points?.push(x, y);
		const nX = -shiftY / diffD;
		const nY = shiftX / diffD;
		const thX = nX * this.#thickness;
		const thY = nY * this.#thickness;
		this.#last.set(this.#last.subarray(2, 8), 0);
		this.#last.set([x2 + thX, y2 + thY], 4);
		this.#last.set(this.#last.subarray(14, 18), 12);
		this.#last.set([x2 - thX, y2 - thY], 16);
		if (isNaN(this.#last[6])) {
			if (this.#top.length === 0) {
				this.#last.set([x1 + thX, y1 + thY], 2);
				this.#top.push(NaN, NaN, NaN, NaN, (x1 + thX - layerX) / layerWidth, (y1 + thY - layerY) / layerHeight);
				this.#last.set([x1 - thX, y1 - thY], 14);
				this.#bottom.push(NaN, NaN, NaN, NaN, (x1 - thX - layerX) / layerWidth, (y1 - thY - layerY) / layerHeight);
			}
			this.#last.set([
				x0,
				y0,
				x1,
				y1,
				x2,
				y2
			], 6);
			return !this.isEmpty();
		}
		this.#last.set([
			x0,
			y0,
			x1,
			y1,
			x2,
			y2
		], 6);
		if (Math.abs(Math.atan2(y0 - y1, x0 - x1) - Math.atan2(shiftY, shiftX)) < Math.PI / 2) {
			[x1, y1, x2, y2] = this.#last.subarray(2, 6);
			this.#top.push(NaN, NaN, NaN, NaN, ((x1 + x2) / 2 - layerX) / layerWidth, ((y1 + y2) / 2 - layerY) / layerHeight);
			[x1, y1, x0, y0] = this.#last.subarray(14, 18);
			this.#bottom.push(NaN, NaN, NaN, NaN, ((x0 + x1) / 2 - layerX) / layerWidth, ((y0 + y1) / 2 - layerY) / layerHeight);
			return true;
		}
		[x0, y0, x1, y1, x2, y2] = this.#last.subarray(0, 6);
		this.#top.push(((x0 + 5 * x1) / 6 - layerX) / layerWidth, ((y0 + 5 * y1) / 6 - layerY) / layerHeight, ((5 * x1 + x2) / 6 - layerX) / layerWidth, ((5 * y1 + y2) / 6 - layerY) / layerHeight, ((x1 + x2) / 2 - layerX) / layerWidth, ((y1 + y2) / 2 - layerY) / layerHeight);
		[x2, y2, x1, y1, x0, y0] = this.#last.subarray(12, 18);
		this.#bottom.push(((x0 + 5 * x1) / 6 - layerX) / layerWidth, ((y0 + 5 * y1) / 6 - layerY) / layerHeight, ((5 * x1 + x2) / 6 - layerX) / layerWidth, ((5 * y1 + y2) / 6 - layerY) / layerHeight, ((x1 + x2) / 2 - layerX) / layerWidth, ((y1 + y2) / 2 - layerY) / layerHeight);
		return true;
	}
	toSVGPath() {
		if (this.isEmpty()) return "";
		const top = this.#top;
		const bottom = this.#bottom;
		if (isNaN(this.#last[6]) && !this.isEmpty()) return this.#toSVGPathTwoPoints();
		const buffer = [];
		buffer.push(`M${top[4]} ${top[5]}`);
		for (let i = 6; i < top.length; i += 6) if (isNaN(top[i])) buffer.push(`L${top[i + 4]} ${top[i + 5]}`);
		else buffer.push(`C${top[i]} ${top[i + 1]} ${top[i + 2]} ${top[i + 3]} ${top[i + 4]} ${top[i + 5]}`);
		this.#toSVGPathEnd(buffer);
		for (let i = bottom.length - 6; i >= 6; i -= 6) if (isNaN(bottom[i])) buffer.push(`L${bottom[i + 4]} ${bottom[i + 5]}`);
		else buffer.push(`C${bottom[i]} ${bottom[i + 1]} ${bottom[i + 2]} ${bottom[i + 3]} ${bottom[i + 4]} ${bottom[i + 5]}`);
		this.#toSVGPathStart(buffer);
		return buffer.join(" ");
	}
	#toSVGPathTwoPoints() {
		const [x, y, width, height] = this.#box;
		const [lastTopX, lastTopY, lastBottomX, lastBottomY] = this.#getLastCoords();
		return `M${(this.#last[2] - x) / width} ${(this.#last[3] - y) / height} L${(this.#last[4] - x) / width} ${(this.#last[5] - y) / height} L${lastTopX} ${lastTopY} L${lastBottomX} ${lastBottomY} L${(this.#last[16] - x) / width} ${(this.#last[17] - y) / height} L${(this.#last[14] - x) / width} ${(this.#last[15] - y) / height} Z`;
	}
	#toSVGPathStart(buffer) {
		const bottom = this.#bottom;
		buffer.push(`L${bottom[4]} ${bottom[5]} Z`);
	}
	#toSVGPathEnd(buffer) {
		const [x, y, width, height] = this.#box;
		const lastTop = this.#last.subarray(4, 6);
		const lastBottom = this.#last.subarray(16, 18);
		const [lastTopX, lastTopY, lastBottomX, lastBottomY] = this.#getLastCoords();
		buffer.push(`L${(lastTop[0] - x) / width} ${(lastTop[1] - y) / height} L${lastTopX} ${lastTopY} L${lastBottomX} ${lastBottomY} L${(lastBottom[0] - x) / width} ${(lastBottom[1] - y) / height}`);
	}
	newFreeDrawOutline(outline, points, box, scaleFactor, innerMargin, isLTR) {
		return new FreeDrawOutline(outline, points, box, scaleFactor, innerMargin, isLTR);
	}
	getOutlines() {
		const top = this.#top;
		const bottom = this.#bottom;
		const last = this.#last;
		const [layerX, layerY, layerWidth, layerHeight] = this.#box;
		const points = new Float32Array((this.#points?.length ?? 0) + 2);
		for (let i = 0, ii = points.length - 2; i < ii; i += 2) {
			points[i] = (this.#points[i] - layerX) / layerWidth;
			points[i + 1] = (this.#points[i + 1] - layerY) / layerHeight;
		}
		points[points.length - 2] = (this.#lastX - layerX) / layerWidth;
		points[points.length - 1] = (this.#lastY - layerY) / layerHeight;
		if (isNaN(last[6]) && !this.isEmpty()) return this.#getOutlineTwoPoints(points);
		const outline = new Float32Array(this.#top.length + 24 + this.#bottom.length);
		let N = top.length;
		for (let i = 0; i < N; i += 2) {
			if (isNaN(top[i])) {
				outline[i] = outline[i + 1] = NaN;
				continue;
			}
			outline[i] = top[i];
			outline[i + 1] = top[i + 1];
		}
		N = this.#getOutlineEnd(outline, N);
		for (let i = bottom.length - 6; i >= 6; i -= 6) for (let j = 0; j < 6; j += 2) {
			if (isNaN(bottom[i + j])) {
				outline[N] = outline[N + 1] = NaN;
				N += 2;
				continue;
			}
			outline[N] = bottom[i + j];
			outline[N + 1] = bottom[i + j + 1];
			N += 2;
		}
		this.#getOutlineStart(outline, N);
		return this.newFreeDrawOutline(outline, points, this.#box, this.#scaleFactor, this.#innerMargin, this.#isLTR);
	}
	#getOutlineTwoPoints(points) {
		const last = this.#last;
		const [layerX, layerY, layerWidth, layerHeight] = this.#box;
		const [lastTopX, lastTopY, lastBottomX, lastBottomY] = this.#getLastCoords();
		const outline = /* @__PURE__ */ new Float32Array(36);
		outline.set([
			NaN,
			NaN,
			NaN,
			NaN,
			(last[2] - layerX) / layerWidth,
			(last[3] - layerY) / layerHeight,
			NaN,
			NaN,
			NaN,
			NaN,
			(last[4] - layerX) / layerWidth,
			(last[5] - layerY) / layerHeight,
			NaN,
			NaN,
			NaN,
			NaN,
			lastTopX,
			lastTopY,
			NaN,
			NaN,
			NaN,
			NaN,
			lastBottomX,
			lastBottomY,
			NaN,
			NaN,
			NaN,
			NaN,
			(last[16] - layerX) / layerWidth,
			(last[17] - layerY) / layerHeight,
			NaN,
			NaN,
			NaN,
			NaN,
			(last[14] - layerX) / layerWidth,
			(last[15] - layerY) / layerHeight
		], 0);
		return this.newFreeDrawOutline(outline, points, this.#box, this.#scaleFactor, this.#innerMargin, this.#isLTR);
	}
	#getOutlineStart(outline, pos) {
		const bottom = this.#bottom;
		outline.set([
			NaN,
			NaN,
			NaN,
			NaN,
			bottom[4],
			bottom[5]
		], pos);
		return pos += 6;
	}
	#getOutlineEnd(outline, pos) {
		const lastTop = this.#last.subarray(4, 6);
		const lastBottom = this.#last.subarray(16, 18);
		const [layerX, layerY, layerWidth, layerHeight] = this.#box;
		const [lastTopX, lastTopY, lastBottomX, lastBottomY] = this.#getLastCoords();
		outline.set([
			NaN,
			NaN,
			NaN,
			NaN,
			(lastTop[0] - layerX) / layerWidth,
			(lastTop[1] - layerY) / layerHeight,
			NaN,
			NaN,
			NaN,
			NaN,
			lastTopX,
			lastTopY,
			NaN,
			NaN,
			NaN,
			NaN,
			lastBottomX,
			lastBottomY,
			NaN,
			NaN,
			NaN,
			NaN,
			(lastBottom[0] - layerX) / layerWidth,
			(lastBottom[1] - layerY) / layerHeight
		], pos);
		return pos += 24;
	}
};
var FreeDrawOutline = class extends Outline {
	#box;
	#bbox = /* @__PURE__ */ new Float32Array(4);
	#innerMargin;
	#isLTR;
	#points;
	#scaleFactor;
	#outline;
	constructor(outline, points, box, scaleFactor, innerMargin, isLTR) {
		super();
		this.#outline = outline;
		this.#points = points;
		this.#box = box;
		this.#scaleFactor = scaleFactor;
		this.#innerMargin = innerMargin;
		this.#isLTR = isLTR;
		this.lastPoint = [NaN, NaN];
		this.#computeMinMax(isLTR);
		const [x, y, width, height] = this.#bbox;
		for (let i = 0, ii = outline.length; i < ii; i += 2) {
			outline[i] = (outline[i] - x) / width;
			outline[i + 1] = (outline[i + 1] - y) / height;
		}
		for (let i = 0, ii = points.length; i < ii; i += 2) {
			points[i] = (points[i] - x) / width;
			points[i + 1] = (points[i + 1] - y) / height;
		}
	}
	toSVGPath() {
		const buffer = [`M${this.#outline[4]} ${this.#outline[5]}`];
		for (let i = 6, ii = this.#outline.length; i < ii; i += 6) {
			if (isNaN(this.#outline[i])) {
				buffer.push(`L${this.#outline[i + 4]} ${this.#outline[i + 5]}`);
				continue;
			}
			buffer.push(`C${this.#outline[i]} ${this.#outline[i + 1]} ${this.#outline[i + 2]} ${this.#outline[i + 3]} ${this.#outline[i + 4]} ${this.#outline[i + 5]}`);
		}
		buffer.push("Z");
		return buffer.join(" ");
	}
	serialize([blX, blY, trX, trY], rotation) {
		const width = trX - blX;
		const height = trY - blY;
		let outline;
		let points;
		switch (rotation) {
			case 0:
				outline = Outline._rescale(this.#outline, blX, trY, width, -height);
				points = Outline._rescale(this.#points, blX, trY, width, -height);
				break;
			case 90:
				outline = Outline._rescaleAndSwap(this.#outline, blX, blY, width, height);
				points = Outline._rescaleAndSwap(this.#points, blX, blY, width, height);
				break;
			case 180:
				outline = Outline._rescale(this.#outline, trX, blY, -width, height);
				points = Outline._rescale(this.#points, trX, blY, -width, height);
				break;
			case 270:
				outline = Outline._rescaleAndSwap(this.#outline, trX, trY, -width, -height);
				points = Outline._rescaleAndSwap(this.#points, trX, trY, -width, -height);
		}
		return {
			outline: Array.from(outline),
			points: [Array.from(points)]
		};
	}
	#computeMinMax(isLTR) {
		const outline = this.#outline;
		let lastX = outline[4];
		let lastY = outline[5];
		let minX = lastX;
		let minY = lastY;
		let maxX = lastX;
		let maxY = lastY;
		let lastPointX = lastX;
		let lastPointY = lastY;
		const ltrCallback = isLTR ? Math.max : Math.min;
		for (let i = 6, ii = outline.length; i < ii; i += 6) {
			if (isNaN(outline[i])) {
				minX = Math.min(minX, outline[i + 4]);
				minY = Math.min(minY, outline[i + 5]);
				maxX = Math.max(maxX, outline[i + 4]);
				maxY = Math.max(maxY, outline[i + 5]);
				if (lastPointY < outline[i + 5]) {
					lastPointX = outline[i + 4];
					lastPointY = outline[i + 5];
				} else if (lastPointY === outline[i + 5]) lastPointX = ltrCallback(lastPointX, outline[i + 4]);
			} else {
				const bbox = Util$1.bezierBoundingBox(lastX, lastY, ...outline.slice(i, i + 6));
				minX = Math.min(minX, bbox[0]);
				minY = Math.min(minY, bbox[1]);
				maxX = Math.max(maxX, bbox[2]);
				maxY = Math.max(maxY, bbox[3]);
				if (lastPointY < bbox[3]) {
					lastPointX = bbox[2];
					lastPointY = bbox[3];
				} else if (lastPointY === bbox[3]) lastPointX = ltrCallback(lastPointX, bbox[2]);
			}
			lastX = outline[i + 4];
			lastY = outline[i + 5];
		}
		const bbox = this.#bbox;
		bbox[0] = minX - this.#innerMargin;
		bbox[1] = minY - this.#innerMargin;
		bbox[2] = maxX - minX + 2 * this.#innerMargin;
		bbox[3] = maxY - minY + 2 * this.#innerMargin;
		this.lastPoint = [lastPointX, lastPointY];
	}
	get box() {
		return this.#bbox;
	}
	newOutliner(point, box, scaleFactor, thickness, isLTR, innerMargin = 0) {
		return new FreeDrawOutliner(point, box, scaleFactor, thickness, isLTR, innerMargin);
	}
	getNewOutline(thickness, innerMargin) {
		const [x, y, width, height] = this.#bbox;
		const [layerX, layerY, layerWidth, layerHeight] = this.#box;
		const sx = width * layerWidth;
		const sy = height * layerHeight;
		const tx = x * layerWidth + layerX;
		const ty = y * layerHeight + layerY;
		const outliner = this.newOutliner({
			x: this.#points[0] * sx + tx,
			y: this.#points[1] * sy + ty
		}, this.#box, this.#scaleFactor, thickness, this.#isLTR, innerMargin ?? this.#innerMargin);
		for (let i = 2; i < this.#points.length; i += 2) outliner.add({
			x: this.#points[i] * sx + tx,
			y: this.#points[i + 1] * sy + ty
		});
		return outliner.getOutlines();
	}
};
var HighlightOutliner = class {
	#box;
	#lastPoint;
	#verticalEdges = [];
	#intervals = [];
	constructor(boxes, borderWidth = 0, innerMargin = 0, isLTR = true) {
		let minX = Infinity;
		let maxX = -Infinity;
		let minY = Infinity;
		let maxY = -Infinity;
		const EPSILON = 10 ** -4;
		for (const { x, y, width, height } of boxes) {
			const x1 = Math.floor((x - borderWidth) / EPSILON) * EPSILON;
			const x2 = Math.ceil((x + width + borderWidth) / EPSILON) * EPSILON;
			const y1 = Math.floor((y - borderWidth) / EPSILON) * EPSILON;
			const y2 = Math.ceil((y + height + borderWidth) / EPSILON) * EPSILON;
			const left = [
				x1,
				y1,
				y2,
				true
			];
			const right = [
				x2,
				y1,
				y2,
				false
			];
			this.#verticalEdges.push(left, right);
			minX = Math.min(minX, x1);
			maxX = Math.max(maxX, x2);
			minY = Math.min(minY, y1);
			maxY = Math.max(maxY, y2);
		}
		const bboxWidth = maxX - minX + 2 * innerMargin;
		const bboxHeight = maxY - minY + 2 * innerMargin;
		const shiftedMinX = minX - innerMargin;
		const shiftedMinY = minY - innerMargin;
		const lastEdge = this.#verticalEdges.at(isLTR ? -1 : -2);
		const lastPoint = [lastEdge[0], lastEdge[2]];
		for (const edge of this.#verticalEdges) {
			const [x, y1, y2] = edge;
			edge[0] = (x - shiftedMinX) / bboxWidth;
			edge[1] = (y1 - shiftedMinY) / bboxHeight;
			edge[2] = (y2 - shiftedMinY) / bboxHeight;
		}
		this.#box = new Float32Array([
			shiftedMinX,
			shiftedMinY,
			bboxWidth,
			bboxHeight
		]);
		this.#lastPoint = lastPoint;
	}
	getOutlines() {
		this.#verticalEdges.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
		const outlineVerticalEdges = [];
		for (const edge of this.#verticalEdges) if (edge[3]) {
			outlineVerticalEdges.push(...this.#breakEdge(edge));
			this.#insert(edge);
		} else {
			this.#remove(edge);
			outlineVerticalEdges.push(...this.#breakEdge(edge));
		}
		return this.#getOutlines(outlineVerticalEdges);
	}
	#getOutlines(outlineVerticalEdges) {
		const edges = [];
		const allEdges = /* @__PURE__ */ new Set();
		for (const edge of outlineVerticalEdges) {
			const [x, y1, y2] = edge;
			edges.push([
				x,
				y1,
				edge
			], [
				x,
				y2,
				edge
			]);
		}
		edges.sort((a, b) => a[1] - b[1] || a[0] - b[0]);
		for (let i = 0, ii = edges.length; i < ii; i += 2) {
			const edge1 = edges[i][2];
			const edge2 = edges[i + 1][2];
			edge1.push(edge2);
			edge2.push(edge1);
			allEdges.add(edge1);
			allEdges.add(edge2);
		}
		const outlines = [];
		let outline;
		while (allEdges.size > 0) {
			const edge = allEdges.values().next().value;
			let [x, y1, y2, edge1, edge2] = edge;
			allEdges.delete(edge);
			let lastPointX = x;
			let lastPointY = y1;
			outline = [x, y2];
			outlines.push(outline);
			while (true) {
				let e;
				if (allEdges.has(edge1)) e = edge1;
				else if (allEdges.has(edge2)) e = edge2;
				else break;
				allEdges.delete(e);
				[x, y1, y2, edge1, edge2] = e;
				if (lastPointX !== x) {
					outline.push(lastPointX, lastPointY, x, lastPointY === y1 ? y1 : y2);
					lastPointX = x;
				}
				lastPointY = lastPointY === y1 ? y2 : y1;
			}
			outline.push(lastPointX, lastPointY);
		}
		return new HighlightOutline(outlines, this.#box, this.#lastPoint);
	}
	#binarySearch(y) {
		const array = this.#intervals;
		let start = 0;
		let end = array.length - 1;
		while (start <= end) {
			const middle = start + end >> 1;
			const y1 = array[middle][0];
			if (y1 === y) return middle;
			if (y1 < y) start = middle + 1;
			else end = middle - 1;
		}
		return end + 1;
	}
	#insert([, y1, y2]) {
		const index = this.#binarySearch(y1);
		this.#intervals.splice(index, 0, [y1, y2]);
	}
	#remove([, y1, y2]) {
		const index = this.#binarySearch(y1);
		for (let i = index; i < this.#intervals.length; i++) {
			const [start, end] = this.#intervals[i];
			if (start !== y1) break;
			if (start === y1 && end === y2) {
				this.#intervals.splice(i, 1);
				return;
			}
		}
		for (let i = index - 1; i >= 0; i--) {
			const [start, end] = this.#intervals[i];
			if (start !== y1) break;
			if (start === y1 && end === y2) {
				this.#intervals.splice(i, 1);
				return;
			}
		}
	}
	#breakEdge(edge) {
		const [x, y1, y2] = edge;
		const results = [[
			x,
			y1,
			y2
		]];
		const index = this.#binarySearch(y2);
		for (let i = 0; i < index; i++) {
			const [start, end] = this.#intervals[i];
			for (let j = 0, jj = results.length; j < jj; j++) {
				const [, y3, y4] = results[j];
				if (end <= y3 || y4 <= start) continue;
				if (y3 >= start) {
					if (y4 > end) results[j][1] = end;
					else {
						if (jj === 1) return [];
						results.splice(j, 1);
						j--;
						jj--;
					}
					continue;
				}
				results[j][2] = start;
				if (y4 > end) results.push([
					x,
					end,
					y4
				]);
			}
		}
		return results;
	}
};
var HighlightOutline = class extends Outline {
	#box;
	#outlines;
	constructor(outlines, box, lastPoint) {
		super();
		this.#outlines = outlines;
		this.#box = box;
		this.lastPoint = lastPoint;
	}
	toSVGPath() {
		const buffer = [];
		for (const polygon of this.#outlines) {
			let [prevX, prevY] = polygon;
			buffer.push(`M${prevX} ${prevY}`);
			for (let i = 2; i < polygon.length; i += 2) {
				const x = polygon[i];
				const y = polygon[i + 1];
				if (x === prevX) {
					buffer.push(`V${y}`);
					prevY = y;
				} else if (y === prevY) {
					buffer.push(`H${x}`);
					prevX = x;
				}
			}
			buffer.push("Z");
		}
		return buffer.join(" ");
	}
	serialize([blX, blY, trX, trY], _rotation) {
		const outlines = [];
		const width = trX - blX;
		const height = trY - blY;
		for (const outline of this.#outlines) {
			const points = new Array(outline.length);
			for (let i = 0; i < outline.length; i += 2) {
				points[i] = blX + outline[i] * width;
				points[i + 1] = trY - outline[i + 1] * height;
			}
			outlines.push(points);
		}
		return outlines;
	}
	get box() {
		return this.#box;
	}
	get classNamesForOutlining() {
		return ["highlightOutline"];
	}
};
var FreeHighlightOutliner = class extends FreeDrawOutliner {
	newFreeDrawOutline(outline, points, box, scaleFactor, innerMargin, isLTR) {
		return new FreeHighlightOutline(outline, points, box, scaleFactor, innerMargin, isLTR);
	}
};
var FreeHighlightOutline = class extends FreeDrawOutline {
	newOutliner(point, box, scaleFactor, thickness, isLTR, innerMargin = 0) {
		return new FreeHighlightOutliner(point, box, scaleFactor, thickness, isLTR, innerMargin);
	}
};
var ColorPicker$1 = class ColorPicker$1 {
	#button = null;
	#buttonSwatch = null;
	#defaultColor;
	#dropdown = null;
	#dropdownWasFromKeyboard = false;
	#isMainColorPicker = false;
	#editor = null;
	#eventBus;
	#openDropdownAC = null;
	#uiManager = null;
	#type;
	static #l10nColor = null;
	static get _keyboardManager() {
		return shadow$1(this, "_keyboardManager", new KeyboardManager([
			[["Escape", "mac+Escape"], ColorPicker$1.prototype._hideDropdownFromKeyboard],
			[[" ", "mac+ "], ColorPicker$1.prototype._colorSelectFromKeyboard],
			[[
				"ArrowDown",
				"ArrowRight",
				"mac+ArrowDown",
				"mac+ArrowRight"
			], ColorPicker$1.prototype._moveToNext],
			[[
				"ArrowUp",
				"ArrowLeft",
				"mac+ArrowUp",
				"mac+ArrowLeft"
			], ColorPicker$1.prototype._moveToPrevious],
			[["Home", "mac+Home"], ColorPicker$1.prototype._moveToBeginning],
			[["End", "mac+End"], ColorPicker$1.prototype._moveToEnd]
		]));
	}
	constructor({ editor = null, uiManager = null }) {
		if (editor) {
			this.#isMainColorPicker = false;
			this.#type = AnnotationEditorParamsType$1.HIGHLIGHT_COLOR;
			this.#editor = editor;
		} else {
			this.#isMainColorPicker = true;
			this.#type = AnnotationEditorParamsType$1.HIGHLIGHT_DEFAULT_COLOR;
		}
		this.#uiManager = editor?._uiManager || uiManager;
		this.#eventBus = this.#uiManager._eventBus;
		this.#defaultColor = editor?.color || this.#uiManager?.highlightColors.values().next().value || "#FFFF98";
		ColorPicker$1.#l10nColor ||= Object.freeze({
			blue: "pdfjs-editor-colorpicker-blue",
			green: "pdfjs-editor-colorpicker-green",
			pink: "pdfjs-editor-colorpicker-pink",
			red: "pdfjs-editor-colorpicker-red",
			yellow: "pdfjs-editor-colorpicker-yellow"
		});
	}
	renderButton() {
		const button = this.#button = document.createElement("button");
		button.className = "colorPicker";
		button.tabIndex = "0";
		button.setAttribute("data-l10n-id", "pdfjs-editor-colorpicker-button");
		button.setAttribute("aria-haspopup", true);
		const signal = this.#uiManager._signal;
		button.addEventListener("click", this.#openDropdown.bind(this), { signal });
		button.addEventListener("keydown", this.#keyDown.bind(this), { signal });
		const swatch = this.#buttonSwatch = document.createElement("span");
		swatch.className = "swatch";
		swatch.setAttribute("aria-hidden", true);
		swatch.style.backgroundColor = this.#defaultColor;
		button.append(swatch);
		return button;
	}
	renderMainDropdown() {
		const dropdown = this.#dropdown = this.#getDropdownRoot();
		dropdown.setAttribute("aria-orientation", "horizontal");
		dropdown.setAttribute("aria-labelledby", "highlightColorPickerLabel");
		return dropdown;
	}
	#getDropdownRoot() {
		const div = document.createElement("div");
		const signal = this.#uiManager._signal;
		div.addEventListener("contextmenu", noContextMenu$1, { signal });
		div.className = "dropdown";
		div.role = "listbox";
		div.setAttribute("aria-multiselectable", false);
		div.setAttribute("aria-orientation", "vertical");
		div.setAttribute("data-l10n-id", "pdfjs-editor-colorpicker-dropdown");
		for (const [name, color] of this.#uiManager.highlightColors) {
			const button = document.createElement("button");
			button.tabIndex = "0";
			button.role = "option";
			button.setAttribute("data-color", color);
			button.title = name;
			button.setAttribute("data-l10n-id", ColorPicker$1.#l10nColor[name]);
			const swatch = document.createElement("span");
			button.append(swatch);
			swatch.className = "swatch";
			swatch.style.backgroundColor = color;
			button.setAttribute("aria-selected", color === this.#defaultColor);
			button.addEventListener("click", this.#colorSelect.bind(this, color), { signal });
			div.append(button);
		}
		div.addEventListener("keydown", this.#keyDown.bind(this), { signal });
		return div;
	}
	#colorSelect(color, event) {
		event.stopPropagation();
		this.#eventBus.dispatch("switchannotationeditorparams", {
			source: this,
			type: this.#type,
			value: color
		});
	}
	_colorSelectFromKeyboard(event) {
		if (event.target === this.#button) {
			this.#openDropdown(event);
			return;
		}
		const color = event.target.getAttribute("data-color");
		if (!color) return;
		this.#colorSelect(color, event);
	}
	_moveToNext(event) {
		if (!this.#isDropdownVisible) {
			this.#openDropdown(event);
			return;
		}
		if (event.target === this.#button) {
			this.#dropdown.firstChild?.focus();
			return;
		}
		event.target.nextSibling?.focus();
	}
	_moveToPrevious(event) {
		if (event.target === this.#dropdown?.firstChild || event.target === this.#button) {
			if (this.#isDropdownVisible) this._hideDropdownFromKeyboard();
			return;
		}
		if (!this.#isDropdownVisible) this.#openDropdown(event);
		event.target.previousSibling?.focus();
	}
	_moveToBeginning(event) {
		if (!this.#isDropdownVisible) {
			this.#openDropdown(event);
			return;
		}
		this.#dropdown.firstChild?.focus();
	}
	_moveToEnd(event) {
		if (!this.#isDropdownVisible) {
			this.#openDropdown(event);
			return;
		}
		this.#dropdown.lastChild?.focus();
	}
	#keyDown(event) {
		ColorPicker$1._keyboardManager.exec(this, event);
	}
	#openDropdown(event) {
		if (this.#isDropdownVisible) {
			this.hideDropdown();
			return;
		}
		this.#dropdownWasFromKeyboard = event.detail === 0;
		if (!this.#openDropdownAC) {
			this.#openDropdownAC = new AbortController();
			window.addEventListener("pointerdown", this.#pointerDown.bind(this), { signal: this.#uiManager.combinedSignal(this.#openDropdownAC) });
		}
		if (this.#dropdown) {
			this.#dropdown.classList.remove("hidden");
			return;
		}
		const root = this.#dropdown = this.#getDropdownRoot();
		this.#button.append(root);
	}
	#pointerDown(event) {
		if (this.#dropdown?.contains(event.target)) return;
		this.hideDropdown();
	}
	hideDropdown() {
		this.#dropdown?.classList.add("hidden");
		this.#openDropdownAC?.abort();
		this.#openDropdownAC = null;
	}
	get #isDropdownVisible() {
		return this.#dropdown && !this.#dropdown.classList.contains("hidden");
	}
	_hideDropdownFromKeyboard() {
		if (this.#isMainColorPicker) return;
		if (!this.#isDropdownVisible) {
			this.#editor?.unselect();
			return;
		}
		this.hideDropdown();
		this.#button.focus({
			preventScroll: true,
			focusVisible: this.#dropdownWasFromKeyboard
		});
	}
	updateColor(color) {
		if (this.#buttonSwatch) this.#buttonSwatch.style.backgroundColor = color;
		if (!this.#dropdown) return;
		const i = this.#uiManager.highlightColors.values();
		for (const child of this.#dropdown.children) child.setAttribute("aria-selected", i.next().value === color);
	}
	destroy() {
		this.#button?.remove();
		this.#button = null;
		this.#buttonSwatch = null;
		this.#dropdown?.remove();
		this.#dropdown = null;
	}
};
var HighlightEditor = class HighlightEditor extends AnnotationEditor {
	#anchorNode = null;
	#anchorOffset = 0;
	#boxes;
	#clipPathId = null;
	#colorPicker = null;
	#focusOutlines = null;
	#focusNode = null;
	#focusOffset = 0;
	#highlightDiv = null;
	#highlightOutlines = null;
	#id = null;
	#isFreeHighlight = false;
	#lastPoint = null;
	#opacity;
	#outlineId = null;
	#text = "";
	#thickness;
	#methodOfCreation = "";
	static _defaultColor = null;
	static _defaultOpacity = 1;
	static _defaultThickness = 12;
	static _type = "highlight";
	static _editorType = AnnotationEditorType$1.HIGHLIGHT;
	static _freeHighlightId = -1;
	static _freeHighlight = null;
	static _freeHighlightClipId = "";
	static get _keyboardManager() {
		const proto = HighlightEditor.prototype;
		return shadow$1(this, "_keyboardManager", new KeyboardManager([
			[
				["ArrowLeft", "mac+ArrowLeft"],
				proto._moveCaret,
				{ args: [0] }
			],
			[
				["ArrowRight", "mac+ArrowRight"],
				proto._moveCaret,
				{ args: [1] }
			],
			[
				["ArrowUp", "mac+ArrowUp"],
				proto._moveCaret,
				{ args: [2] }
			],
			[
				["ArrowDown", "mac+ArrowDown"],
				proto._moveCaret,
				{ args: [3] }
			]
		]));
	}
	constructor(params) {
		super({
			...params,
			name: "highlightEditor"
		});
		this.color = params.color || HighlightEditor._defaultColor;
		this.#thickness = params.thickness || HighlightEditor._defaultThickness;
		this.#opacity = params.opacity || HighlightEditor._defaultOpacity;
		this.#boxes = params.boxes || null;
		this.#methodOfCreation = params.methodOfCreation || "";
		this.#text = params.text || "";
		this._isDraggable = false;
		if (params.highlightId > -1) {
			this.#isFreeHighlight = true;
			this.#createFreeOutlines(params);
			this.#addToDrawLayer();
		} else if (this.#boxes) {
			this.#anchorNode = params.anchorNode;
			this.#anchorOffset = params.anchorOffset;
			this.#focusNode = params.focusNode;
			this.#focusOffset = params.focusOffset;
			this.#createOutlines();
			this.#addToDrawLayer();
			this.rotate(this.rotation);
		}
	}
	get telemetryInitialData() {
		return {
			action: "added",
			type: this.#isFreeHighlight ? "free_highlight" : "highlight",
			color: this._uiManager.highlightColorNames.get(this.color),
			thickness: this.#thickness,
			methodOfCreation: this.#methodOfCreation
		};
	}
	get telemetryFinalData() {
		return {
			type: "highlight",
			color: this._uiManager.highlightColorNames.get(this.color)
		};
	}
	static computeTelemetryFinalData(data) {
		return { numberOfColors: data.get("color").size };
	}
	#createOutlines() {
		const outliner = new HighlightOutliner(this.#boxes, .001);
		this.#highlightOutlines = outliner.getOutlines();
		[this.x, this.y, this.width, this.height] = this.#highlightOutlines.box;
		const outlinerForOutline = new HighlightOutliner(this.#boxes, .0025, .001, this._uiManager.direction === "ltr");
		this.#focusOutlines = outlinerForOutline.getOutlines();
		const { lastPoint } = this.#focusOutlines;
		this.#lastPoint = [(lastPoint[0] - this.x) / this.width, (lastPoint[1] - this.y) / this.height];
	}
	#createFreeOutlines({ highlightOutlines, highlightId, clipPathId }) {
		this.#highlightOutlines = highlightOutlines;
		const extraThickness = 1.5;
		this.#focusOutlines = highlightOutlines.getNewOutline(this.#thickness / 2 + extraThickness, .0025);
		if (highlightId >= 0) {
			this.#id = highlightId;
			this.#clipPathId = clipPathId;
			this.parent.drawLayer.finalizeDraw(highlightId, {
				bbox: highlightOutlines.box,
				path: { d: highlightOutlines.toSVGPath() }
			});
			this.#outlineId = this.parent.drawLayer.drawOutline({
				rootClass: {
					highlightOutline: true,
					free: true
				},
				bbox: this.#focusOutlines.box,
				path: { d: this.#focusOutlines.toSVGPath() }
			}, true);
		} else if (this.parent) {
			const angle = this.parent.viewport.rotation;
			this.parent.drawLayer.updateProperties(this.#id, {
				bbox: HighlightEditor.#rotateBbox(this.#highlightOutlines.box, (angle - this.rotation + 360) % 360),
				path: { d: highlightOutlines.toSVGPath() }
			});
			this.parent.drawLayer.updateProperties(this.#outlineId, {
				bbox: HighlightEditor.#rotateBbox(this.#focusOutlines.box, angle),
				path: { d: this.#focusOutlines.toSVGPath() }
			});
		}
		const [x, y, width, height] = highlightOutlines.box;
		switch (this.rotation) {
			case 0:
				this.x = x;
				this.y = y;
				this.width = width;
				this.height = height;
				break;
			case 90: {
				const [pageWidth, pageHeight] = this.parentDimensions;
				this.x = y;
				this.y = 1 - x;
				this.width = width * pageHeight / pageWidth;
				this.height = height * pageWidth / pageHeight;
				break;
			}
			case 180:
				this.x = 1 - x;
				this.y = 1 - y;
				this.width = width;
				this.height = height;
				break;
			case 270: {
				const [pageWidth, pageHeight] = this.parentDimensions;
				this.x = 1 - y;
				this.y = x;
				this.width = width * pageHeight / pageWidth;
				this.height = height * pageWidth / pageHeight;
				break;
			}
		}
		const { lastPoint } = this.#focusOutlines;
		this.#lastPoint = [(lastPoint[0] - x) / width, (lastPoint[1] - y) / height];
	}
	static initialize(l10n, uiManager) {
		AnnotationEditor.initialize(l10n, uiManager);
		HighlightEditor._defaultColor ||= uiManager.highlightColors?.values().next().value || "#fff066";
	}
	static updateDefaultParams(type, value) {
		switch (type) {
			case AnnotationEditorParamsType$1.HIGHLIGHT_DEFAULT_COLOR:
				HighlightEditor._defaultColor = value;
				break;
			case AnnotationEditorParamsType$1.HIGHLIGHT_THICKNESS: HighlightEditor._defaultThickness = value;
		}
	}
	translateInPage(x, y) {}
	get toolbarPosition() {
		return this.#lastPoint;
	}
	updateParams(type, value) {
		switch (type) {
			case AnnotationEditorParamsType$1.HIGHLIGHT_COLOR:
				this.#updateColor(value);
				break;
			case AnnotationEditorParamsType$1.HIGHLIGHT_THICKNESS: this.#updateThickness(value);
		}
	}
	static get defaultPropertiesToUpdate() {
		return [[AnnotationEditorParamsType$1.HIGHLIGHT_DEFAULT_COLOR, HighlightEditor._defaultColor], [AnnotationEditorParamsType$1.HIGHLIGHT_THICKNESS, HighlightEditor._defaultThickness]];
	}
	get propertiesToUpdate() {
		return [
			[AnnotationEditorParamsType$1.HIGHLIGHT_COLOR, this.color || HighlightEditor._defaultColor],
			[AnnotationEditorParamsType$1.HIGHLIGHT_THICKNESS, this.#thickness || HighlightEditor._defaultThickness],
			[AnnotationEditorParamsType$1.HIGHLIGHT_FREE, this.#isFreeHighlight]
		];
	}
	#updateColor(color) {
		const setColorAndOpacity = (col, opa) => {
			this.color = col;
			this.#opacity = opa;
			this.parent?.drawLayer.updateProperties(this.#id, { root: {
				fill: col,
				"fill-opacity": opa
			} });
			this.#colorPicker?.updateColor(col);
		};
		const savedColor = this.color;
		const savedOpacity = this.#opacity;
		this.addCommands({
			cmd: setColorAndOpacity.bind(this, color, HighlightEditor._defaultOpacity),
			undo: setColorAndOpacity.bind(this, savedColor, savedOpacity),
			post: this._uiManager.updateUI.bind(this._uiManager, this),
			mustExec: true,
			type: AnnotationEditorParamsType$1.HIGHLIGHT_COLOR,
			overwriteIfSameType: true,
			keepUndo: true
		});
		this._reportTelemetry({
			action: "color_changed",
			color: this._uiManager.highlightColorNames.get(color)
		}, true);
	}
	#updateThickness(thickness) {
		const savedThickness = this.#thickness;
		const setThickness = (th) => {
			this.#thickness = th;
			this.#changeThickness(th);
		};
		this.addCommands({
			cmd: setThickness.bind(this, thickness),
			undo: setThickness.bind(this, savedThickness),
			post: this._uiManager.updateUI.bind(this._uiManager, this),
			mustExec: true,
			type: AnnotationEditorParamsType$1.INK_THICKNESS,
			overwriteIfSameType: true,
			keepUndo: true
		});
		this._reportTelemetry({
			action: "thickness_changed",
			thickness
		}, true);
	}
	async addEditToolbar() {
		const toolbar = await super.addEditToolbar();
		if (!toolbar) return null;
		if (this._uiManager.highlightColors) {
			this.#colorPicker = new ColorPicker$1({ editor: this });
			toolbar.addColorPicker(this.#colorPicker);
		}
		return toolbar;
	}
	disableEditing() {
		super.disableEditing();
		this.div.classList.toggle("disabled", true);
	}
	enableEditing() {
		super.enableEditing();
		this.div.classList.toggle("disabled", false);
	}
	fixAndSetPosition() {
		return super.fixAndSetPosition(this.#getRotation());
	}
	getBaseTranslation() {
		return [0, 0];
	}
	getRect(tx, ty) {
		return super.getRect(tx, ty, this.#getRotation());
	}
	onceAdded(focus) {
		if (!this.annotationElementId) this.parent.addUndoableEditor(this);
		if (focus) this.div.focus();
	}
	remove() {
		this.#cleanDrawLayer();
		this._reportTelemetry({ action: "deleted" });
		super.remove();
	}
	rebuild() {
		if (!this.parent) return;
		super.rebuild();
		if (this.div === null) return;
		this.#addToDrawLayer();
		if (!this.isAttachedToDOM) this.parent.add(this);
	}
	setParent(parent) {
		let mustBeSelected = false;
		if (this.parent && !parent) this.#cleanDrawLayer();
		else if (parent) {
			this.#addToDrawLayer(parent);
			mustBeSelected = !this.parent && this.div?.classList.contains("selectedEditor");
		}
		super.setParent(parent);
		this.show(this._isVisible);
		if (mustBeSelected) this.select();
	}
	#changeThickness(thickness) {
		if (!this.#isFreeHighlight) return;
		this.#createFreeOutlines({ highlightOutlines: this.#highlightOutlines.getNewOutline(thickness / 2) });
		this.fixAndSetPosition();
		const [parentWidth, parentHeight] = this.parentDimensions;
		this.setDims(this.width * parentWidth, this.height * parentHeight);
	}
	#cleanDrawLayer() {
		if (this.#id === null || !this.parent) return;
		this.parent.drawLayer.remove(this.#id);
		this.#id = null;
		this.parent.drawLayer.remove(this.#outlineId);
		this.#outlineId = null;
	}
	#addToDrawLayer(parent = this.parent) {
		if (this.#id !== null) return;
		({id: this.#id, clipPathId: this.#clipPathId} = parent.drawLayer.draw({
			bbox: this.#highlightOutlines.box,
			root: {
				viewBox: "0 0 1 1",
				fill: this.color,
				"fill-opacity": this.#opacity
			},
			rootClass: {
				highlight: true,
				free: this.#isFreeHighlight
			},
			path: { d: this.#highlightOutlines.toSVGPath() }
		}, false, true));
		this.#outlineId = parent.drawLayer.drawOutline({
			rootClass: {
				highlightOutline: true,
				free: this.#isFreeHighlight
			},
			bbox: this.#focusOutlines.box,
			path: { d: this.#focusOutlines.toSVGPath() }
		}, this.#isFreeHighlight);
		if (this.#highlightDiv) this.#highlightDiv.style.clipPath = this.#clipPathId;
	}
	static #rotateBbox([x, y, width, height], angle) {
		switch (angle) {
			case 90: return [
				1 - y - height,
				x,
				height,
				width
			];
			case 180: return [
				1 - x - width,
				1 - y - height,
				width,
				height
			];
			case 270: return [
				y,
				1 - x - width,
				height,
				width
			];
		}
		return [
			x,
			y,
			width,
			height
		];
	}
	rotate(angle) {
		const { drawLayer } = this.parent;
		let box;
		if (this.#isFreeHighlight) {
			angle = (angle - this.rotation + 360) % 360;
			box = HighlightEditor.#rotateBbox(this.#highlightOutlines.box, angle);
		} else box = HighlightEditor.#rotateBbox([
			this.x,
			this.y,
			this.width,
			this.height
		], angle);
		drawLayer.updateProperties(this.#id, {
			bbox: box,
			root: { "data-main-rotation": angle }
		});
		drawLayer.updateProperties(this.#outlineId, {
			bbox: HighlightEditor.#rotateBbox(this.#focusOutlines.box, angle),
			root: { "data-main-rotation": angle }
		});
	}
	render() {
		if (this.div) return this.div;
		const div = super.render();
		if (this.#text) {
			div.setAttribute("aria-label", this.#text);
			div.setAttribute("role", "mark");
		}
		if (this.#isFreeHighlight) div.classList.add("free");
		else this.div.addEventListener("keydown", this.#keydown.bind(this), { signal: this._uiManager._signal });
		const highlightDiv = this.#highlightDiv = document.createElement("div");
		div.append(highlightDiv);
		highlightDiv.setAttribute("aria-hidden", "true");
		highlightDiv.className = "internal";
		highlightDiv.style.clipPath = this.#clipPathId;
		const [parentWidth, parentHeight] = this.parentDimensions;
		this.setDims(this.width * parentWidth, this.height * parentHeight);
		bindEvents(this, this.#highlightDiv, ["pointerover", "pointerleave"]);
		this.enableEditing();
		return div;
	}
	pointerover() {
		if (!this.isSelected) this.parent?.drawLayer.updateProperties(this.#outlineId, { rootClass: { hovered: true } });
	}
	pointerleave() {
		if (!this.isSelected) this.parent?.drawLayer.updateProperties(this.#outlineId, { rootClass: { hovered: false } });
	}
	#keydown(event) {
		HighlightEditor._keyboardManager.exec(this, event);
	}
	_moveCaret(direction) {
		this.parent.unselect(this);
		switch (direction) {
			case 0:
			case 2:
				this.#setCaret(true);
				break;
			case 1:
			case 3: this.#setCaret(false);
		}
	}
	#setCaret(start) {
		if (!this.#anchorNode) return;
		const selection = window.getSelection();
		if (start) selection.setPosition(this.#anchorNode, this.#anchorOffset);
		else selection.setPosition(this.#focusNode, this.#focusOffset);
	}
	select() {
		super.select();
		if (!this.#outlineId) return;
		this.parent?.drawLayer.updateProperties(this.#outlineId, { rootClass: {
			hovered: false,
			selected: true
		} });
	}
	unselect() {
		super.unselect();
		if (!this.#outlineId) return;
		this.parent?.drawLayer.updateProperties(this.#outlineId, { rootClass: { selected: false } });
		if (!this.#isFreeHighlight) this.#setCaret(false);
	}
	get _mustFixPosition() {
		return !this.#isFreeHighlight;
	}
	show(visible = this._isVisible) {
		super.show(visible);
		if (this.parent) {
			this.parent.drawLayer.updateProperties(this.#id, { rootClass: { hidden: !visible } });
			this.parent.drawLayer.updateProperties(this.#outlineId, { rootClass: { hidden: !visible } });
		}
	}
	#getRotation() {
		return this.#isFreeHighlight ? this.rotation : 0;
	}
	#serializeBoxes() {
		if (this.#isFreeHighlight) return null;
		const [pageWidth, pageHeight] = this.pageDimensions;
		const [pageX, pageY] = this.pageTranslation;
		const boxes = this.#boxes;
		const quadPoints = new Float32Array(boxes.length * 8);
		let i = 0;
		for (const { x, y, width, height } of boxes) {
			const sx = x * pageWidth + pageX;
			const sy = (1 - y) * pageHeight + pageY;
			quadPoints[i] = quadPoints[i + 4] = sx;
			quadPoints[i + 1] = quadPoints[i + 3] = sy;
			quadPoints[i + 2] = quadPoints[i + 6] = sx + width * pageWidth;
			quadPoints[i + 5] = quadPoints[i + 7] = sy - height * pageHeight;
			i += 8;
		}
		return quadPoints;
	}
	#serializeOutlines(rect) {
		return this.#highlightOutlines.serialize(rect, this.#getRotation());
	}
	static startHighlighting(parent, isLTR, { target: textLayer, x, y }) {
		const { x: layerX, y: layerY, width: parentWidth, height: parentHeight } = textLayer.getBoundingClientRect();
		const ac = new AbortController();
		const signal = parent.combinedSignal(ac);
		const pointerUpCallback = (e) => {
			ac.abort();
			this.#endHighlight(parent, e);
		};
		window.addEventListener("blur", pointerUpCallback, { signal });
		window.addEventListener("pointerup", pointerUpCallback, { signal });
		window.addEventListener("pointerdown", stopEvent$1, {
			capture: true,
			passive: false,
			signal
		});
		window.addEventListener("contextmenu", noContextMenu$1, { signal });
		textLayer.addEventListener("pointermove", this.#highlightMove.bind(this, parent), { signal });
		this._freeHighlight = new FreeHighlightOutliner({
			x,
			y
		}, [
			layerX,
			layerY,
			parentWidth,
			parentHeight
		], parent.scale, this._defaultThickness / 2, isLTR, .001);
		({id: this._freeHighlightId, clipPathId: this._freeHighlightClipId} = parent.drawLayer.draw({
			bbox: [
				0,
				0,
				1,
				1
			],
			root: {
				viewBox: "0 0 1 1",
				fill: this._defaultColor,
				"fill-opacity": this._defaultOpacity
			},
			rootClass: {
				highlight: true,
				free: true
			},
			path: { d: this._freeHighlight.toSVGPath() }
		}, true, true));
	}
	static #highlightMove(parent, event) {
		if (this._freeHighlight.add(event)) parent.drawLayer.updateProperties(this._freeHighlightId, { path: { d: this._freeHighlight.toSVGPath() } });
	}
	static #endHighlight(parent, event) {
		if (!this._freeHighlight.isEmpty()) parent.createAndAddNewEditor(event, false, {
			highlightId: this._freeHighlightId,
			highlightOutlines: this._freeHighlight.getOutlines(),
			clipPathId: this._freeHighlightClipId,
			methodOfCreation: "main_toolbar"
		});
		else parent.drawLayer.remove(this._freeHighlightId);
		this._freeHighlightId = -1;
		this._freeHighlight = null;
		this._freeHighlightClipId = "";
	}
	static async deserialize(data, parent, uiManager) {
		let initialData = null;
		if (data instanceof HighlightAnnotationElement) {
			const { data: { quadPoints, rect, rotation, id, color, opacity, popupRef }, parent: { page: { pageNumber } } } = data;
			initialData = data = {
				annotationType: AnnotationEditorType$1.HIGHLIGHT,
				color: Array.from(color),
				opacity,
				quadPoints,
				boxes: null,
				pageIndex: pageNumber - 1,
				rect: rect.slice(0),
				rotation,
				id,
				deleted: false,
				popupRef
			};
		} else if (data instanceof InkAnnotationElement) {
			const { data: { inkLists, rect, rotation, id, color, borderStyle: { rawWidth: thickness }, popupRef }, parent: { page: { pageNumber } } } = data;
			initialData = data = {
				annotationType: AnnotationEditorType$1.HIGHLIGHT,
				color: Array.from(color),
				thickness,
				inkLists,
				boxes: null,
				pageIndex: pageNumber - 1,
				rect: rect.slice(0),
				rotation,
				id,
				deleted: false,
				popupRef
			};
		}
		const { color, quadPoints, inkLists, opacity } = data;
		const editor = await super.deserialize(data, parent, uiManager);
		editor.color = Util$1.makeHexColor(...color);
		editor.#opacity = opacity || 1;
		if (inkLists) editor.#thickness = data.thickness;
		editor.annotationElementId = data.id || null;
		editor._initialData = initialData;
		const [pageWidth, pageHeight] = editor.pageDimensions;
		const [pageX, pageY] = editor.pageTranslation;
		if (quadPoints) {
			const boxes = editor.#boxes = [];
			for (let i = 0; i < quadPoints.length; i += 8) boxes.push({
				x: (quadPoints[i] - pageX) / pageWidth,
				y: 1 - (quadPoints[i + 1] - pageY) / pageHeight,
				width: (quadPoints[i + 2] - quadPoints[i]) / pageWidth,
				height: (quadPoints[i + 1] - quadPoints[i + 5]) / pageHeight
			});
			editor.#createOutlines();
			editor.#addToDrawLayer();
			editor.rotate(editor.rotation);
		} else if (inkLists) {
			editor.#isFreeHighlight = true;
			const points = inkLists[0];
			const point = {
				x: points[0] - pageX,
				y: pageHeight - (points[1] - pageY)
			};
			const outliner = new FreeHighlightOutliner(point, [
				0,
				0,
				pageWidth,
				pageHeight
			], 1, editor.#thickness / 2, true, .001);
			for (let i = 0, ii = points.length; i < ii; i += 2) {
				point.x = points[i] - pageX;
				point.y = pageHeight - (points[i + 1] - pageY);
				outliner.add(point);
			}
			const { id, clipPathId } = parent.drawLayer.draw({
				bbox: [
					0,
					0,
					1,
					1
				],
				root: {
					viewBox: "0 0 1 1",
					fill: editor.color,
					"fill-opacity": editor._defaultOpacity
				},
				rootClass: {
					highlight: true,
					free: true
				},
				path: { d: outliner.toSVGPath() }
			}, true, true);
			editor.#createFreeOutlines({
				highlightOutlines: outliner.getOutlines(),
				highlightId: id,
				clipPathId
			});
			editor.#addToDrawLayer();
		}
		return editor;
	}
	serialize(isForCopying = false) {
		if (this.isEmpty() || isForCopying) return null;
		if (this.deleted) return this.serializeDeleted();
		const rect = this.getRect(0, 0);
		const color = AnnotationEditor._colorManager.convert(this.color);
		const serialized = {
			annotationType: AnnotationEditorType$1.HIGHLIGHT,
			color,
			opacity: this.#opacity,
			thickness: this.#thickness,
			quadPoints: this.#serializeBoxes(),
			outlines: this.#serializeOutlines(rect),
			pageIndex: this.pageIndex,
			rect,
			rotation: this.#getRotation(),
			structTreeParentId: this._structTreeParentId
		};
		if (this.annotationElementId && !this.#hasElementChanged(serialized)) return null;
		serialized.id = this.annotationElementId;
		return serialized;
	}
	#hasElementChanged(serialized) {
		const { color } = this._initialData;
		return serialized.color.some((c, i) => c !== color[i]);
	}
	renderAnnotationElement(annotation) {
		annotation.updateEdited({ rect: this.getRect(0, 0) });
		return null;
	}
	static canCreateNewEmptyEditor() {
		return false;
	}
};
var DrawingOptions = class {
	#svgProperties = Object.create(null);
	updateProperty(name, value) {
		this[name] = value;
		this.updateSVGProperty(name, value);
	}
	updateProperties(properties) {
		if (!properties) return;
		for (const [name, value] of Object.entries(properties)) this.updateProperty(name, value);
	}
	updateSVGProperty(name, value) {
		this.#svgProperties[name] = value;
	}
	toSVGProperties() {
		const root = this.#svgProperties;
		this.#svgProperties = Object.create(null);
		return { root };
	}
	reset() {
		this.#svgProperties = Object.create(null);
	}
	updateAll(options = this) {
		this.updateProperties(options);
	}
	clone() {
		unreachable("Not implemented");
	}
};
var DrawingEditor = class DrawingEditor extends AnnotationEditor {
	#drawOutlines = null;
	#mustBeCommitted;
	_drawId = null;
	static _currentDrawId = -1;
	static _currentParent = null;
	static #currentDraw = null;
	static #currentDrawingAC = null;
	static #currentDrawingOptions = null;
	static #currentPointerId = NaN;
	static #currentPointerType = null;
	static #currentPointerIds = null;
	static #currentMoveTimestamp = NaN;
	static _INNER_MARGIN = 3;
	constructor(params) {
		super(params);
		this.#mustBeCommitted = params.mustBeCommitted || false;
		if (params.drawOutlines) {
			this.#createDrawOutlines(params);
			this.#addToDrawLayer();
		}
	}
	#createDrawOutlines({ drawOutlines, drawId, drawingOptions }) {
		this.#drawOutlines = drawOutlines;
		this._drawingOptions ||= drawingOptions;
		if (drawId >= 0) {
			this._drawId = drawId;
			this.parent.drawLayer.finalizeDraw(drawId, drawOutlines.defaultProperties);
		} else this._drawId = this.#createDrawing(drawOutlines, this.parent);
		this.#updateBbox(drawOutlines.box);
	}
	#createDrawing(drawOutlines, parent) {
		const { id } = parent.drawLayer.draw(DrawingEditor._mergeSVGProperties(this._drawingOptions.toSVGProperties(), drawOutlines.defaultSVGProperties), false, false);
		return id;
	}
	static _mergeSVGProperties(p1, p2) {
		const p1Keys = new Set(Object.keys(p1));
		for (const [key, value] of Object.entries(p2)) if (p1Keys.has(key)) Object.assign(p1[key], value);
		else p1[key] = value;
		return p1;
	}
	static getDefaultDrawingOptions(_options) {
		unreachable("Not implemented");
	}
	static get typesMap() {
		unreachable("Not implemented");
	}
	static get isDrawer() {
		return true;
	}
	static get supportMultipleDrawings() {
		return false;
	}
	static updateDefaultParams(type, value) {
		const propertyName = this.typesMap.get(type);
		if (propertyName) this._defaultDrawingOptions.updateProperty(propertyName, value);
		if (this._currentParent) {
			DrawingEditor.#currentDraw.updateProperty(propertyName, value);
			this._currentParent.drawLayer.updateProperties(this._currentDrawId, this._defaultDrawingOptions.toSVGProperties());
		}
	}
	updateParams(type, value) {
		const propertyName = this.constructor.typesMap.get(type);
		if (propertyName) this._updateProperty(type, propertyName, value);
	}
	static get defaultPropertiesToUpdate() {
		const properties = [];
		const options = this._defaultDrawingOptions;
		for (const [type, name] of this.typesMap) properties.push([type, options[name]]);
		return properties;
	}
	get propertiesToUpdate() {
		const properties = [];
		const { _drawingOptions } = this;
		for (const [type, name] of this.constructor.typesMap) properties.push([type, _drawingOptions[name]]);
		return properties;
	}
	_updateProperty(type, name, value) {
		const options = this._drawingOptions;
		const savedValue = options[name];
		const setter = (val) => {
			options.updateProperty(name, val);
			const bbox = this.#drawOutlines.updateProperty(name, val);
			if (bbox) this.#updateBbox(bbox);
			this.parent?.drawLayer.updateProperties(this._drawId, options.toSVGProperties());
		};
		this.addCommands({
			cmd: setter.bind(this, value),
			undo: setter.bind(this, savedValue),
			post: this._uiManager.updateUI.bind(this._uiManager, this),
			mustExec: true,
			type,
			overwriteIfSameType: true,
			keepUndo: true
		});
	}
	_onResizing() {
		this.parent?.drawLayer.updateProperties(this._drawId, DrawingEditor._mergeSVGProperties(this.#drawOutlines.getPathResizingSVGProperties(this.#convertToDrawSpace()), { bbox: this.#rotateBox() }));
	}
	_onResized() {
		this.parent?.drawLayer.updateProperties(this._drawId, DrawingEditor._mergeSVGProperties(this.#drawOutlines.getPathResizedSVGProperties(this.#convertToDrawSpace()), { bbox: this.#rotateBox() }));
	}
	_onTranslating(x, y) {
		this.parent?.drawLayer.updateProperties(this._drawId, { bbox: this.#rotateBox(x, y) });
	}
	_onTranslated() {
		this.parent?.drawLayer.updateProperties(this._drawId, DrawingEditor._mergeSVGProperties(this.#drawOutlines.getPathTranslatedSVGProperties(this.#convertToDrawSpace(), this.parentDimensions), { bbox: this.#rotateBox() }));
	}
	_onStartDragging() {
		this.parent?.drawLayer.updateProperties(this._drawId, { rootClass: { moving: true } });
	}
	_onStopDragging() {
		this.parent?.drawLayer.updateProperties(this._drawId, { rootClass: { moving: false } });
	}
	commit() {
		super.commit();
		this.disableEditMode();
		this.disableEditing();
	}
	disableEditing() {
		super.disableEditing();
		this.div.classList.toggle("disabled", true);
	}
	enableEditing() {
		super.enableEditing();
		this.div.classList.toggle("disabled", false);
	}
	getBaseTranslation() {
		return [0, 0];
	}
	get isResizable() {
		return true;
	}
	onceAdded(focus) {
		if (!this.annotationElementId) this.parent.addUndoableEditor(this);
		this._isDraggable = true;
		if (this.#mustBeCommitted) {
			this.#mustBeCommitted = false;
			this.commit();
			this.parent.setSelected(this);
			if (focus && this.isOnScreen) this.div.focus();
		}
	}
	remove() {
		this.#cleanDrawLayer();
		super.remove();
	}
	rebuild() {
		if (!this.parent) return;
		super.rebuild();
		if (this.div === null) return;
		this.#addToDrawLayer();
		this.#updateBbox(this.#drawOutlines.box);
		if (!this.isAttachedToDOM) this.parent.add(this);
	}
	setParent(parent) {
		let mustBeSelected = false;
		if (this.parent && !parent) {
			this._uiManager.removeShouldRescale(this);
			this.#cleanDrawLayer();
		} else if (parent) {
			this._uiManager.addShouldRescale(this);
			this.#addToDrawLayer(parent);
			mustBeSelected = !this.parent && this.div?.classList.contains("selectedEditor");
		}
		super.setParent(parent);
		if (mustBeSelected) this.select();
	}
	#cleanDrawLayer() {
		if (this._drawId === null || !this.parent) return;
		this.parent.drawLayer.remove(this._drawId);
		this._drawId = null;
		this._drawingOptions.reset();
	}
	#addToDrawLayer(parent = this.parent) {
		if (this._drawId !== null && this.parent === parent) return;
		if (this._drawId !== null) {
			this.parent.drawLayer.updateParent(this._drawId, parent.drawLayer);
			return;
		}
		this._drawingOptions.updateAll();
		this._drawId = this.#createDrawing(this.#drawOutlines, parent);
	}
	#convertToParentSpace([x, y, width, height]) {
		const { parentDimensions: [pW, pH], rotation } = this;
		switch (rotation) {
			case 90: return [
				y,
				1 - x,
				width * (pH / pW),
				height * (pW / pH)
			];
			case 180: return [
				1 - x,
				1 - y,
				width,
				height
			];
			case 270: return [
				1 - y,
				x,
				width * (pH / pW),
				height * (pW / pH)
			];
			default: return [
				x,
				y,
				width,
				height
			];
		}
	}
	#convertToDrawSpace() {
		const { x, y, width, height, parentDimensions: [pW, pH], rotation } = this;
		switch (rotation) {
			case 90: return [
				1 - y,
				x,
				width * (pW / pH),
				height * (pH / pW)
			];
			case 180: return [
				1 - x,
				1 - y,
				width,
				height
			];
			case 270: return [
				y,
				1 - x,
				width * (pW / pH),
				height * (pH / pW)
			];
			default: return [
				x,
				y,
				width,
				height
			];
		}
	}
	#updateBbox(bbox) {
		[this.x, this.y, this.width, this.height] = this.#convertToParentSpace(bbox);
		if (this.div) {
			this.fixAndSetPosition();
			const [parentWidth, parentHeight] = this.parentDimensions;
			this.setDims(this.width * parentWidth, this.height * parentHeight);
		}
		this._onResized();
	}
	#rotateBox() {
		const { x, y, width, height, rotation, parentRotation, parentDimensions: [pW, pH] } = this;
		switch ((rotation * 4 + parentRotation) / 90) {
			case 1: return [
				1 - y - height,
				x,
				height,
				width
			];
			case 2: return [
				1 - x - width,
				1 - y - height,
				width,
				height
			];
			case 3: return [
				y,
				1 - x - width,
				height,
				width
			];
			case 4: return [
				x,
				y - width * (pW / pH),
				height * (pH / pW),
				width * (pW / pH)
			];
			case 5: return [
				1 - y,
				x,
				width * (pW / pH),
				height * (pH / pW)
			];
			case 6: return [
				1 - x - height * (pH / pW),
				1 - y,
				height * (pH / pW),
				width * (pW / pH)
			];
			case 7: return [
				y - width * (pW / pH),
				1 - x - height * (pH / pW),
				width * (pW / pH),
				height * (pH / pW)
			];
			case 8: return [
				x - width,
				y - height,
				width,
				height
			];
			case 9: return [
				1 - y,
				x - width,
				height,
				width
			];
			case 10: return [
				1 - x,
				1 - y,
				width,
				height
			];
			case 11: return [
				y - height,
				1 - x,
				height,
				width
			];
			case 12: return [
				x - height * (pH / pW),
				y,
				height * (pH / pW),
				width * (pW / pH)
			];
			case 13: return [
				1 - y - width * (pW / pH),
				x - height * (pH / pW),
				width * (pW / pH),
				height * (pH / pW)
			];
			case 14: return [
				1 - x,
				1 - y - width * (pW / pH),
				height * (pH / pW),
				width * (pW / pH)
			];
			case 15: return [
				y,
				1 - x,
				width * (pW / pH),
				height * (pH / pW)
			];
			default: return [
				x,
				y,
				width,
				height
			];
		}
	}
	rotate() {
		if (!this.parent) return;
		this.parent.drawLayer.updateProperties(this._drawId, DrawingEditor._mergeSVGProperties({ bbox: this.#rotateBox() }, this.#drawOutlines.updateRotation((this.parentRotation - this.rotation + 360) % 360)));
	}
	onScaleChanging() {
		if (!this.parent) return;
		this.#updateBbox(this.#drawOutlines.updateParentDimensions(this.parentDimensions, this.parent.scale));
	}
	static onScaleChangingWhenDrawing() {}
	render() {
		if (this.div) return this.div;
		const div = super.render();
		div.classList.add("draw");
		const drawDiv = document.createElement("div");
		div.append(drawDiv);
		drawDiv.setAttribute("aria-hidden", "true");
		drawDiv.className = "internal";
		const [parentWidth, parentHeight] = this.parentDimensions;
		this.setDims(this.width * parentWidth, this.height * parentHeight);
		this._uiManager.addShouldRescale(this);
		this.disableEditing();
		return div;
	}
	static createDrawerInstance(_x, _y, _parentWidth, _parentHeight, _rotation) {
		unreachable("Not implemented");
	}
	static startDrawing(parent, uiManager, _isLTR, event) {
		const { target, offsetX: x, offsetY: y, pointerId, pointerType } = event;
		if (DrawingEditor.#currentPointerType && DrawingEditor.#currentPointerType !== pointerType) return;
		const { viewport: { rotation } } = parent;
		const { width: parentWidth, height: parentHeight } = target.getBoundingClientRect();
		const ac = DrawingEditor.#currentDrawingAC = new AbortController();
		const signal = parent.combinedSignal(ac);
		DrawingEditor.#currentPointerId ||= pointerId;
		DrawingEditor.#currentPointerType ??= pointerType;
		window.addEventListener("pointerup", (e) => {
			if (DrawingEditor.#currentPointerId === e.pointerId) this._endDraw(e);
			else DrawingEditor.#currentPointerIds?.delete(e.pointerId);
		}, { signal });
		window.addEventListener("pointercancel", (e) => {
			if (DrawingEditor.#currentPointerId === e.pointerId) this._currentParent.endDrawingSession();
			else DrawingEditor.#currentPointerIds?.delete(e.pointerId);
		}, { signal });
		window.addEventListener("pointerdown", (e) => {
			if (DrawingEditor.#currentPointerType !== e.pointerType) return;
			(DrawingEditor.#currentPointerIds ||= /* @__PURE__ */ new Set()).add(e.pointerId);
			if (DrawingEditor.#currentDraw.isCancellable()) {
				DrawingEditor.#currentDraw.removeLastElement();
				if (DrawingEditor.#currentDraw.isEmpty()) this._currentParent.endDrawingSession(true);
				else this._endDraw(null);
			}
		}, {
			capture: true,
			passive: false,
			signal
		});
		window.addEventListener("contextmenu", noContextMenu$1, { signal });
		target.addEventListener("pointermove", this._drawMove.bind(this), { signal });
		target.addEventListener("touchmove", (e) => {
			if (e.timeStamp === DrawingEditor.#currentMoveTimestamp) stopEvent$1(e);
		}, { signal });
		parent.toggleDrawing();
		uiManager._editorUndoBar?.hide();
		if (DrawingEditor.#currentDraw) {
			parent.drawLayer.updateProperties(this._currentDrawId, DrawingEditor.#currentDraw.startNew(x, y, parentWidth, parentHeight, rotation));
			return;
		}
		uiManager.updateUIForDefaultProperties(this);
		DrawingEditor.#currentDraw = this.createDrawerInstance(x, y, parentWidth, parentHeight, rotation);
		DrawingEditor.#currentDrawingOptions = this.getDefaultDrawingOptions();
		this._currentParent = parent;
		({id: this._currentDrawId} = parent.drawLayer.draw(this._mergeSVGProperties(DrawingEditor.#currentDrawingOptions.toSVGProperties(), DrawingEditor.#currentDraw.defaultSVGProperties), true, false));
	}
	static _drawMove(event) {
		DrawingEditor.#currentMoveTimestamp = -1;
		if (!DrawingEditor.#currentDraw) return;
		const { offsetX, offsetY, pointerId } = event;
		if (DrawingEditor.#currentPointerId !== pointerId) return;
		if (DrawingEditor.#currentPointerIds?.size >= 1) {
			this._endDraw(event);
			return;
		}
		this._currentParent.drawLayer.updateProperties(this._currentDrawId, DrawingEditor.#currentDraw.add(offsetX, offsetY));
		DrawingEditor.#currentMoveTimestamp = event.timeStamp;
		stopEvent$1(event);
	}
	static _cleanup(all) {
		if (all) {
			this._currentDrawId = -1;
			this._currentParent = null;
			DrawingEditor.#currentDraw = null;
			DrawingEditor.#currentDrawingOptions = null;
			DrawingEditor.#currentPointerType = null;
			DrawingEditor.#currentMoveTimestamp = NaN;
		}
		if (DrawingEditor.#currentDrawingAC) {
			DrawingEditor.#currentDrawingAC.abort();
			DrawingEditor.#currentDrawingAC = null;
			DrawingEditor.#currentPointerId = NaN;
			DrawingEditor.#currentPointerIds = null;
		}
	}
	static _endDraw(event) {
		const parent = this._currentParent;
		if (!parent) return;
		parent.toggleDrawing(true);
		this._cleanup(false);
		if (event) parent.drawLayer.updateProperties(this._currentDrawId, DrawingEditor.#currentDraw.end(event.offsetX, event.offsetY));
		if (this.supportMultipleDrawings) {
			const draw = DrawingEditor.#currentDraw;
			const drawId = this._currentDrawId;
			const lastElement = draw.getLastElement();
			parent.addCommands({
				cmd: () => {
					parent.drawLayer.updateProperties(drawId, draw.setLastElement(lastElement));
				},
				undo: () => {
					parent.drawLayer.updateProperties(drawId, draw.removeLastElement());
				},
				mustExec: false,
				type: AnnotationEditorParamsType$1.DRAW_STEP
			});
			return;
		}
		this.endDrawing(false);
	}
	static endDrawing(isAborted) {
		const parent = this._currentParent;
		if (!parent) return null;
		parent.toggleDrawing(true);
		parent.cleanUndoStack(AnnotationEditorParamsType$1.DRAW_STEP);
		if (!DrawingEditor.#currentDraw.isEmpty()) {
			const { pageDimensions: [pageWidth, pageHeight], scale } = parent;
			const editor = parent.createAndAddNewEditor({
				offsetX: 0,
				offsetY: 0
			}, false, {
				drawId: this._currentDrawId,
				drawOutlines: DrawingEditor.#currentDraw.getOutlines(pageWidth * scale, pageHeight * scale, scale, this._INNER_MARGIN),
				drawingOptions: DrawingEditor.#currentDrawingOptions,
				mustBeCommitted: !isAborted
			});
			this._cleanup(true);
			return editor;
		}
		parent.drawLayer.remove(this._currentDrawId);
		this._cleanup(true);
		return null;
	}
	createDrawingOptions(_data) {}
	static deserializeDraw(_pageX, _pageY, _pageWidth, _pageHeight, _innerWidth, _data) {
		unreachable("Not implemented");
	}
	static async deserialize(data, parent, uiManager) {
		const { rawDims: { pageWidth, pageHeight, pageX, pageY } } = parent.viewport;
		const drawOutlines = this.deserializeDraw(pageX, pageY, pageWidth, pageHeight, this._INNER_MARGIN, data);
		const editor = await super.deserialize(data, parent, uiManager);
		editor.createDrawingOptions(data);
		editor.#createDrawOutlines({ drawOutlines });
		editor.#addToDrawLayer();
		editor.onScaleChanging();
		editor.rotate();
		return editor;
	}
	serializeDraw(isForCopying) {
		const [pageX, pageY] = this.pageTranslation;
		const [pageWidth, pageHeight] = this.pageDimensions;
		return this.#drawOutlines.serialize([
			pageX,
			pageY,
			pageWidth,
			pageHeight
		], isForCopying);
	}
	renderAnnotationElement(annotation) {
		annotation.updateEdited({ rect: this.getRect(0, 0) });
		return null;
	}
	static canCreateNewEmptyEditor() {
		return false;
	}
};
var InkDrawOutliner = class {
	#last = /* @__PURE__ */ new Float64Array(6);
	#line;
	#lines;
	#rotation;
	#thickness;
	#points;
	#lastSVGPath = "";
	#lastIndex = 0;
	#outlines = new InkDrawOutline();
	#parentWidth;
	#parentHeight;
	constructor(x, y, parentWidth, parentHeight, rotation, thickness) {
		this.#parentWidth = parentWidth;
		this.#parentHeight = parentHeight;
		this.#rotation = rotation;
		this.#thickness = thickness;
		[x, y] = this.#normalizePoint(x, y);
		const line = this.#line = [
			NaN,
			NaN,
			NaN,
			NaN,
			x,
			y
		];
		this.#points = [x, y];
		this.#lines = [{
			line,
			points: this.#points
		}];
		this.#last.set(line, 0);
	}
	updateProperty(name, value) {
		if (name === "stroke-width") this.#thickness = value;
	}
	#normalizePoint(x, y) {
		return Outline._normalizePoint(x, y, this.#parentWidth, this.#parentHeight, this.#rotation);
	}
	isEmpty() {
		return !this.#lines || this.#lines.length === 0;
	}
	isCancellable() {
		return this.#points.length <= 10;
	}
	add(x, y) {
		[x, y] = this.#normalizePoint(x, y);
		const [x1, y1, x2, y2] = this.#last.subarray(2, 6);
		const diffX = x - x2;
		const diffY = y - y2;
		if (Math.hypot(this.#parentWidth * diffX, this.#parentHeight * diffY) <= 2) return null;
		this.#points.push(x, y);
		if (isNaN(x1)) {
			this.#last.set([
				x2,
				y2,
				x,
				y
			], 2);
			this.#line.push(NaN, NaN, NaN, NaN, x, y);
			return { path: { d: this.toSVGPath() } };
		}
		if (isNaN(this.#last[0])) this.#line.splice(6, 6);
		this.#last.set([
			x1,
			y1,
			x2,
			y2,
			x,
			y
		], 0);
		this.#line.push(...Outline.createBezierPoints(x1, y1, x2, y2, x, y));
		return { path: { d: this.toSVGPath() } };
	}
	end(x, y) {
		const change = this.add(x, y);
		if (change) return change;
		if (this.#points.length === 2) return { path: { d: this.toSVGPath() } };
		return null;
	}
	startNew(x, y, parentWidth, parentHeight, rotation) {
		this.#parentWidth = parentWidth;
		this.#parentHeight = parentHeight;
		this.#rotation = rotation;
		[x, y] = this.#normalizePoint(x, y);
		const line = this.#line = [
			NaN,
			NaN,
			NaN,
			NaN,
			x,
			y
		];
		this.#points = [x, y];
		const last = this.#lines.at(-1);
		if (last) {
			last.line = new Float32Array(last.line);
			last.points = new Float32Array(last.points);
		}
		this.#lines.push({
			line,
			points: this.#points
		});
		this.#last.set(line, 0);
		this.#lastIndex = 0;
		this.toSVGPath();
		return null;
	}
	getLastElement() {
		return this.#lines.at(-1);
	}
	setLastElement(element) {
		if (!this.#lines) return this.#outlines.setLastElement(element);
		this.#lines.push(element);
		this.#line = element.line;
		this.#points = element.points;
		this.#lastIndex = 0;
		return { path: { d: this.toSVGPath() } };
	}
	removeLastElement() {
		if (!this.#lines) return this.#outlines.removeLastElement();
		this.#lines.pop();
		this.#lastSVGPath = "";
		for (let i = 0, ii = this.#lines.length; i < ii; i++) {
			const { line, points } = this.#lines[i];
			this.#line = line;
			this.#points = points;
			this.#lastIndex = 0;
			this.toSVGPath();
		}
		return { path: { d: this.#lastSVGPath } };
	}
	toSVGPath() {
		const firstX = Outline.svgRound(this.#line[4]);
		const firstY = Outline.svgRound(this.#line[5]);
		if (this.#points.length === 2) {
			this.#lastSVGPath = `${this.#lastSVGPath} M ${firstX} ${firstY} Z`;
			return this.#lastSVGPath;
		}
		if (this.#points.length <= 6) {
			const i = this.#lastSVGPath.lastIndexOf("M");
			this.#lastSVGPath = `${this.#lastSVGPath.slice(0, i)} M ${firstX} ${firstY}`;
			this.#lastIndex = 6;
		}
		if (this.#points.length === 4) {
			const secondX = Outline.svgRound(this.#line[10]);
			const secondY = Outline.svgRound(this.#line[11]);
			this.#lastSVGPath = `${this.#lastSVGPath} L ${secondX} ${secondY}`;
			this.#lastIndex = 12;
			return this.#lastSVGPath;
		}
		const buffer = [];
		if (this.#lastIndex === 0) {
			buffer.push(`M ${firstX} ${firstY}`);
			this.#lastIndex = 6;
		}
		for (let i = this.#lastIndex, ii = this.#line.length; i < ii; i += 6) {
			const [c1x, c1y, c2x, c2y, x, y] = this.#line.slice(i, i + 6).map(Outline.svgRound);
			buffer.push(`C${c1x} ${c1y} ${c2x} ${c2y} ${x} ${y}`);
		}
		this.#lastSVGPath += buffer.join(" ");
		this.#lastIndex = this.#line.length;
		return this.#lastSVGPath;
	}
	getOutlines(parentWidth, parentHeight, scale, innerMargin) {
		const last = this.#lines.at(-1);
		last.line = new Float32Array(last.line);
		last.points = new Float32Array(last.points);
		this.#outlines.build(this.#lines, parentWidth, parentHeight, scale, this.#rotation, this.#thickness, innerMargin);
		this.#last = null;
		this.#line = null;
		this.#lines = null;
		this.#lastSVGPath = null;
		return this.#outlines;
	}
	get defaultSVGProperties() {
		return {
			root: { viewBox: "0 0 10000 10000" },
			rootClass: { draw: true },
			bbox: [
				0,
				0,
				1,
				1
			]
		};
	}
};
var InkDrawOutline = class InkDrawOutline extends Outline {
	#bbox;
	#currentRotation = 0;
	#innerMargin;
	#lines;
	#parentWidth;
	#parentHeight;
	#parentScale;
	#rotation;
	#thickness;
	build(lines, parentWidth, parentHeight, parentScale, rotation, thickness, innerMargin) {
		this.#parentWidth = parentWidth;
		this.#parentHeight = parentHeight;
		this.#parentScale = parentScale;
		this.#rotation = rotation;
		this.#thickness = thickness;
		this.#innerMargin = innerMargin ?? 0;
		this.#lines = lines;
		this.#computeBbox();
	}
	setLastElement(element) {
		this.#lines.push(element);
		return { path: { d: this.toSVGPath() } };
	}
	removeLastElement() {
		this.#lines.pop();
		return { path: { d: this.toSVGPath() } };
	}
	toSVGPath() {
		const buffer = [];
		for (const { line } of this.#lines) {
			buffer.push(`M${Outline.svgRound(line[4])} ${Outline.svgRound(line[5])}`);
			if (line.length === 6) {
				buffer.push("Z");
				continue;
			}
			if (line.length === 12) {
				buffer.push(`L${Outline.svgRound(line[10])} ${Outline.svgRound(line[11])}`);
				continue;
			}
			for (let i = 6, ii = line.length; i < ii; i += 6) {
				const [c1x, c1y, c2x, c2y, x, y] = line.subarray(i, i + 6).map(Outline.svgRound);
				buffer.push(`C${c1x} ${c1y} ${c2x} ${c2y} ${x} ${y}`);
			}
		}
		return buffer.join("");
	}
	serialize([pageX, pageY, pageWidth, pageHeight], isForCopying) {
		const serializedLines = [];
		const serializedPoints = [];
		const [x, y, width, height] = this.#getBBoxWithNoMargin();
		let tx, ty, sx, sy, x1, y1, x2, y2, rescaleFn;
		switch (this.#rotation) {
			case 0:
				rescaleFn = Outline._rescale;
				tx = pageX;
				ty = pageY + pageHeight;
				sx = pageWidth;
				sy = -pageHeight;
				x1 = pageX + x * pageWidth;
				y1 = pageY + (1 - y - height) * pageHeight;
				x2 = pageX + (x + width) * pageWidth;
				y2 = pageY + (1 - y) * pageHeight;
				break;
			case 90:
				rescaleFn = Outline._rescaleAndSwap;
				tx = pageX;
				ty = pageY;
				sx = pageWidth;
				sy = pageHeight;
				x1 = pageX + y * pageWidth;
				y1 = pageY + x * pageHeight;
				x2 = pageX + (y + height) * pageWidth;
				y2 = pageY + (x + width) * pageHeight;
				break;
			case 180:
				rescaleFn = Outline._rescale;
				tx = pageX + pageWidth;
				ty = pageY;
				sx = -pageWidth;
				sy = pageHeight;
				x1 = pageX + (1 - x - width) * pageWidth;
				y1 = pageY + y * pageHeight;
				x2 = pageX + (1 - x) * pageWidth;
				y2 = pageY + (y + height) * pageHeight;
				break;
			case 270:
				rescaleFn = Outline._rescaleAndSwap;
				tx = pageX + pageWidth;
				ty = pageY + pageHeight;
				sx = -pageWidth;
				sy = -pageHeight;
				x1 = pageX + (1 - y - height) * pageWidth;
				y1 = pageY + (1 - x - width) * pageHeight;
				x2 = pageX + (1 - y) * pageWidth;
				y2 = pageY + (1 - x) * pageHeight;
		}
		for (const { line, points } of this.#lines) {
			serializedLines.push(rescaleFn(line, tx, ty, sx, sy, isForCopying ? new Array(line.length) : null));
			serializedPoints.push(rescaleFn(points, tx, ty, sx, sy, isForCopying ? new Array(points.length) : null));
		}
		return {
			lines: serializedLines,
			points: serializedPoints,
			rect: [
				x1,
				y1,
				x2,
				y2
			]
		};
	}
	static deserialize(pageX, pageY, pageWidth, pageHeight, innerMargin, { paths: { lines, points }, rotation, thickness }) {
		const newLines = [];
		let tx, ty, sx, sy, rescaleFn;
		switch (rotation) {
			case 0:
				rescaleFn = Outline._rescale;
				tx = -pageX / pageWidth;
				ty = pageY / pageHeight + 1;
				sx = 1 / pageWidth;
				sy = -1 / pageHeight;
				break;
			case 90:
				rescaleFn = Outline._rescaleAndSwap;
				tx = -pageY / pageHeight;
				ty = -pageX / pageWidth;
				sx = 1 / pageHeight;
				sy = 1 / pageWidth;
				break;
			case 180:
				rescaleFn = Outline._rescale;
				tx = pageX / pageWidth + 1;
				ty = -pageY / pageHeight;
				sx = -1 / pageWidth;
				sy = 1 / pageHeight;
				break;
			case 270:
				rescaleFn = Outline._rescaleAndSwap;
				tx = pageY / pageHeight + 1;
				ty = pageX / pageWidth + 1;
				sx = -1 / pageHeight;
				sy = -1 / pageWidth;
		}
		if (!lines) {
			lines = [];
			for (const point of points) {
				const len = point.length;
				if (len === 2) {
					lines.push(new Float32Array([
						NaN,
						NaN,
						NaN,
						NaN,
						point[0],
						point[1]
					]));
					continue;
				}
				if (len === 4) {
					lines.push(new Float32Array([
						NaN,
						NaN,
						NaN,
						NaN,
						point[0],
						point[1],
						NaN,
						NaN,
						NaN,
						NaN,
						point[2],
						point[3]
					]));
					continue;
				}
				const line = new Float32Array(3 * (len - 2));
				lines.push(line);
				let [x1, y1, x2, y2] = point.subarray(0, 4);
				line.set([
					NaN,
					NaN,
					NaN,
					NaN,
					x1,
					y1
				], 0);
				for (let i = 4; i < len; i += 2) {
					const x = point[i];
					const y = point[i + 1];
					line.set(Outline.createBezierPoints(x1, y1, x2, y2, x, y), (i - 2) * 3);
					[x1, y1, x2, y2] = [
						x2,
						y2,
						x,
						y
					];
				}
			}
		}
		for (let i = 0, ii = lines.length; i < ii; i++) newLines.push({
			line: rescaleFn(lines[i].map((x) => x ?? NaN), tx, ty, sx, sy),
			points: rescaleFn(points[i].map((x) => x ?? NaN), tx, ty, sx, sy)
		});
		const outlines = new InkDrawOutline();
		outlines.build(newLines, pageWidth, pageHeight, 1, rotation, thickness, innerMargin);
		return outlines;
	}
	#getMarginComponents(thickness = this.#thickness) {
		const margin = this.#innerMargin + thickness / 2 * this.#parentScale;
		return this.#rotation % 180 === 0 ? [margin / this.#parentWidth, margin / this.#parentHeight] : [margin / this.#parentHeight, margin / this.#parentWidth];
	}
	#getBBoxWithNoMargin() {
		const [x, y, width, height] = this.#bbox;
		const [marginX, marginY] = this.#getMarginComponents(0);
		return [
			x + marginX,
			y + marginY,
			width - 2 * marginX,
			height - 2 * marginY
		];
	}
	#computeBbox() {
		const bbox = this.#bbox = new Float32Array([
			Infinity,
			Infinity,
			-Infinity,
			-Infinity
		]);
		for (const { line } of this.#lines) {
			if (line.length <= 12) {
				for (let i = 4, ii = line.length; i < ii; i += 6) {
					const [x, y] = line.subarray(i, i + 2);
					bbox[0] = Math.min(bbox[0], x);
					bbox[1] = Math.min(bbox[1], y);
					bbox[2] = Math.max(bbox[2], x);
					bbox[3] = Math.max(bbox[3], y);
				}
				continue;
			}
			let lastX = line[4], lastY = line[5];
			for (let i = 6, ii = line.length; i < ii; i += 6) {
				const [c1x, c1y, c2x, c2y, x, y] = line.subarray(i, i + 6);
				Util$1.bezierBoundingBox(lastX, lastY, c1x, c1y, c2x, c2y, x, y, bbox);
				lastX = x;
				lastY = y;
			}
		}
		const [marginX, marginY] = this.#getMarginComponents();
		bbox[0] = Math.min(1, Math.max(0, bbox[0] - marginX));
		bbox[1] = Math.min(1, Math.max(0, bbox[1] - marginY));
		bbox[2] = Math.min(1, Math.max(0, bbox[2] + marginX));
		bbox[3] = Math.min(1, Math.max(0, bbox[3] + marginY));
		bbox[2] -= bbox[0];
		bbox[3] -= bbox[1];
	}
	get box() {
		return this.#bbox;
	}
	updateProperty(name, value) {
		if (name === "stroke-width") return this.#updateThickness(value);
		return null;
	}
	#updateThickness(thickness) {
		const [oldMarginX, oldMarginY] = this.#getMarginComponents();
		this.#thickness = thickness;
		const [newMarginX, newMarginY] = this.#getMarginComponents();
		const [diffMarginX, diffMarginY] = [newMarginX - oldMarginX, newMarginY - oldMarginY];
		const bbox = this.#bbox;
		bbox[0] -= diffMarginX;
		bbox[1] -= diffMarginY;
		bbox[2] += 2 * diffMarginX;
		bbox[3] += 2 * diffMarginY;
		return bbox;
	}
	updateParentDimensions([width, height], scale) {
		const [oldMarginX, oldMarginY] = this.#getMarginComponents();
		this.#parentWidth = width;
		this.#parentHeight = height;
		this.#parentScale = scale;
		const [newMarginX, newMarginY] = this.#getMarginComponents();
		const diffMarginX = newMarginX - oldMarginX;
		const diffMarginY = newMarginY - oldMarginY;
		const bbox = this.#bbox;
		bbox[0] -= diffMarginX;
		bbox[1] -= diffMarginY;
		bbox[2] += 2 * diffMarginX;
		bbox[3] += 2 * diffMarginY;
		return bbox;
	}
	updateRotation(rotation) {
		this.#currentRotation = rotation;
		return { path: { transform: this.rotationTransform } };
	}
	get viewBox() {
		return this.#bbox.map(Outline.svgRound).join(" ");
	}
	get defaultProperties() {
		const [x, y] = this.#bbox;
		return {
			root: { viewBox: this.viewBox },
			path: { "transform-origin": `${Outline.svgRound(x)} ${Outline.svgRound(y)}` }
		};
	}
	get rotationTransform() {
		const [, , width, height] = this.#bbox;
		let a = 0, b = 0, c = 0, d = 0, e = 0, f = 0;
		switch (this.#currentRotation) {
			case 90:
				b = height / width;
				c = -width / height;
				e = width;
				break;
			case 180:
				a = -1;
				d = -1;
				e = width;
				f = height;
				break;
			case 270:
				b = -height / width;
				c = width / height;
				f = height;
				break;
			default: return "";
		}
		return `matrix(${a} ${b} ${c} ${d} ${Outline.svgRound(e)} ${Outline.svgRound(f)})`;
	}
	getPathResizingSVGProperties([newX, newY, newWidth, newHeight]) {
		const [marginX, marginY] = this.#getMarginComponents();
		const [x, y, width, height] = this.#bbox;
		if (Math.abs(width - marginX) <= Outline.PRECISION || Math.abs(height - marginY) <= Outline.PRECISION) {
			const tx = newX + newWidth / 2 - (x + width / 2);
			const ty = newY + newHeight / 2 - (y + height / 2);
			return { path: {
				"transform-origin": `${Outline.svgRound(newX)} ${Outline.svgRound(newY)}`,
				transform: `${this.rotationTransform} translate(${tx} ${ty})`
			} };
		}
		const s1x = (newWidth - 2 * marginX) / (width - 2 * marginX);
		const s1y = (newHeight - 2 * marginY) / (height - 2 * marginY);
		const s2x = width / newWidth;
		const s2y = height / newHeight;
		return { path: {
			"transform-origin": `${Outline.svgRound(x)} ${Outline.svgRound(y)}`,
			transform: `${this.rotationTransform} scale(${s2x} ${s2y}) translate(${Outline.svgRound(marginX)} ${Outline.svgRound(marginY)}) scale(${s1x} ${s1y}) translate(${Outline.svgRound(-marginX)} ${Outline.svgRound(-marginY)})`
		} };
	}
	getPathResizedSVGProperties([newX, newY, newWidth, newHeight]) {
		const [marginX, marginY] = this.#getMarginComponents();
		const bbox = this.#bbox;
		const [x, y, width, height] = bbox;
		bbox[0] = newX;
		bbox[1] = newY;
		bbox[2] = newWidth;
		bbox[3] = newHeight;
		if (Math.abs(width - marginX) <= Outline.PRECISION || Math.abs(height - marginY) <= Outline.PRECISION) {
			const tx = newX + newWidth / 2 - (x + width / 2);
			const ty = newY + newHeight / 2 - (y + height / 2);
			for (const { line, points } of this.#lines) {
				Outline._translate(line, tx, ty, line);
				Outline._translate(points, tx, ty, points);
			}
			return {
				root: { viewBox: this.viewBox },
				path: {
					"transform-origin": `${Outline.svgRound(newX)} ${Outline.svgRound(newY)}`,
					transform: this.rotationTransform || null,
					d: this.toSVGPath()
				}
			};
		}
		const s1x = (newWidth - 2 * marginX) / (width - 2 * marginX);
		const s1y = (newHeight - 2 * marginY) / (height - 2 * marginY);
		const tx = -s1x * (x + marginX) + newX + marginX;
		const ty = -s1y * (y + marginY) + newY + marginY;
		if (s1x !== 1 || s1y !== 1 || tx !== 0 || ty !== 0) for (const { line, points } of this.#lines) {
			Outline._rescale(line, tx, ty, s1x, s1y, line);
			Outline._rescale(points, tx, ty, s1x, s1y, points);
		}
		return {
			root: { viewBox: this.viewBox },
			path: {
				"transform-origin": `${Outline.svgRound(newX)} ${Outline.svgRound(newY)}`,
				transform: this.rotationTransform || null,
				d: this.toSVGPath()
			}
		};
	}
	getPathTranslatedSVGProperties([newX, newY], parentDimensions) {
		const [newParentWidth, newParentHeight] = parentDimensions;
		const bbox = this.#bbox;
		const tx = newX - bbox[0];
		const ty = newY - bbox[1];
		if (this.#parentWidth === newParentWidth && this.#parentHeight === newParentHeight) for (const { line, points } of this.#lines) {
			Outline._translate(line, tx, ty, line);
			Outline._translate(points, tx, ty, points);
		}
		else {
			const sx = this.#parentWidth / newParentWidth;
			const sy = this.#parentHeight / newParentHeight;
			this.#parentWidth = newParentWidth;
			this.#parentHeight = newParentHeight;
			for (const { line, points } of this.#lines) {
				Outline._rescale(line, tx, ty, sx, sy, line);
				Outline._rescale(points, tx, ty, sx, sy, points);
			}
			bbox[2] *= sx;
			bbox[3] *= sy;
		}
		bbox[0] = newX;
		bbox[1] = newY;
		return {
			root: { viewBox: this.viewBox },
			path: {
				d: this.toSVGPath(),
				"transform-origin": `${Outline.svgRound(newX)} ${Outline.svgRound(newY)}`
			}
		};
	}
	get defaultSVGProperties() {
		const bbox = this.#bbox;
		return {
			root: { viewBox: this.viewBox },
			rootClass: { draw: true },
			path: {
				d: this.toSVGPath(),
				"transform-origin": `${Outline.svgRound(bbox[0])} ${Outline.svgRound(bbox[1])}`,
				transform: this.rotationTransform || null
			},
			bbox
		};
	}
};
var InkDrawingOptions = class InkDrawingOptions extends DrawingOptions {
	#viewParameters;
	constructor(viewerParameters) {
		super();
		this.#viewParameters = viewerParameters;
		super.updateProperties({
			fill: "none",
			stroke: AnnotationEditor._defaultLineColor,
			"stroke-opacity": 1,
			"stroke-width": 1,
			"stroke-linecap": "round",
			"stroke-linejoin": "round",
			"stroke-miterlimit": 10
		});
	}
	updateSVGProperty(name, value) {
		if (name === "stroke-width") {
			value ??= this["stroke-width"];
			value *= this.#viewParameters.realScale;
		}
		super.updateSVGProperty(name, value);
	}
	clone() {
		const clone = new InkDrawingOptions(this.#viewParameters);
		clone.updateAll(this);
		return clone;
	}
};
var InkEditor = class InkEditor extends DrawingEditor {
	static _type = "ink";
	static _editorType = AnnotationEditorType$1.INK;
	static _defaultDrawingOptions = null;
	constructor(params) {
		super({
			...params,
			name: "inkEditor"
		});
		this._willKeepAspectRatio = true;
	}
	static initialize(l10n, uiManager) {
		AnnotationEditor.initialize(l10n, uiManager);
		this._defaultDrawingOptions = new InkDrawingOptions(uiManager.viewParameters);
	}
	static getDefaultDrawingOptions(options) {
		const clone = this._defaultDrawingOptions.clone();
		clone.updateProperties(options);
		return clone;
	}
	static get supportMultipleDrawings() {
		return true;
	}
	static get typesMap() {
		return shadow$1(this, "typesMap", /* @__PURE__ */ new Map([
			[AnnotationEditorParamsType$1.INK_THICKNESS, "stroke-width"],
			[AnnotationEditorParamsType$1.INK_COLOR, "stroke"],
			[AnnotationEditorParamsType$1.INK_OPACITY, "stroke-opacity"]
		]));
	}
	static createDrawerInstance(x, y, parentWidth, parentHeight, rotation) {
		return new InkDrawOutliner(x, y, parentWidth, parentHeight, rotation, this._defaultDrawingOptions["stroke-width"]);
	}
	static deserializeDraw(pageX, pageY, pageWidth, pageHeight, innerMargin, data) {
		return InkDrawOutline.deserialize(pageX, pageY, pageWidth, pageHeight, innerMargin, data);
	}
	static async deserialize(data, parent, uiManager) {
		let initialData = null;
		if (data instanceof InkAnnotationElement) {
			const { data: { inkLists, rect, rotation, id, color, opacity, borderStyle: { rawWidth: thickness }, popupRef }, parent: { page: { pageNumber } } } = data;
			initialData = data = {
				annotationType: AnnotationEditorType$1.INK,
				color: Array.from(color),
				thickness,
				opacity,
				paths: { points: inkLists },
				boxes: null,
				pageIndex: pageNumber - 1,
				rect: rect.slice(0),
				rotation,
				id,
				deleted: false,
				popupRef
			};
		}
		const editor = await super.deserialize(data, parent, uiManager);
		editor.annotationElementId = data.id || null;
		editor._initialData = initialData;
		return editor;
	}
	onScaleChanging() {
		if (!this.parent) return;
		super.onScaleChanging();
		const { _drawId, _drawingOptions, parent } = this;
		_drawingOptions.updateSVGProperty("stroke-width");
		parent.drawLayer.updateProperties(_drawId, _drawingOptions.toSVGProperties());
	}
	static onScaleChangingWhenDrawing() {
		const parent = this._currentParent;
		if (!parent) return;
		super.onScaleChangingWhenDrawing();
		this._defaultDrawingOptions.updateSVGProperty("stroke-width");
		parent.drawLayer.updateProperties(this._currentDrawId, this._defaultDrawingOptions.toSVGProperties());
	}
	createDrawingOptions({ color, thickness, opacity }) {
		this._drawingOptions = InkEditor.getDefaultDrawingOptions({
			stroke: Util$1.makeHexColor(...color),
			"stroke-width": thickness,
			"stroke-opacity": opacity
		});
	}
	serialize(isForCopying = false) {
		if (this.isEmpty()) return null;
		if (this.deleted) return this.serializeDeleted();
		const { lines, points, rect } = this.serializeDraw(isForCopying);
		const { _drawingOptions: { stroke, "stroke-opacity": opacity, "stroke-width": thickness } } = this;
		const serialized = {
			annotationType: AnnotationEditorType$1.INK,
			color: AnnotationEditor._colorManager.convert(stroke),
			opacity,
			thickness,
			paths: {
				lines,
				points
			},
			pageIndex: this.pageIndex,
			rect,
			rotation: this.rotation,
			structTreeParentId: this._structTreeParentId
		};
		if (isForCopying) return serialized;
		if (this.annotationElementId && !this.#hasElementChanged(serialized)) return null;
		serialized.id = this.annotationElementId;
		return serialized;
	}
	#hasElementChanged(serialized) {
		const { color, thickness, opacity, pageIndex } = this._initialData;
		return this._hasBeenMoved || this._hasBeenResized || serialized.color.some((c, i) => c !== color[i]) || serialized.thickness !== thickness || serialized.opacity !== opacity || serialized.pageIndex !== pageIndex;
	}
	renderAnnotationElement(annotation) {
		const { points, rect } = this.serializeDraw(false);
		annotation.updateEdited({
			rect,
			thickness: this._drawingOptions["stroke-width"],
			points
		});
		return null;
	}
};
var StampEditor = class StampEditor extends AnnotationEditor {
	#bitmap = null;
	#bitmapId = null;
	#bitmapPromise = null;
	#bitmapUrl = null;
	#bitmapFile = null;
	#bitmapFileName = "";
	#canvas = null;
	#resizeTimeoutId = null;
	#isSvg = false;
	#hasBeenAddedInUndoStack = false;
	static _type = "stamp";
	static _editorType = AnnotationEditorType$1.STAMP;
	constructor(params) {
		super({
			...params,
			name: "stampEditor"
		});
		this.#bitmapUrl = params.bitmapUrl;
		this.#bitmapFile = params.bitmapFile;
	}
	static initialize(l10n, uiManager) {
		AnnotationEditor.initialize(l10n, uiManager);
	}
	static get supportedTypes() {
		return shadow$1(this, "supportedTypes", [
			"apng",
			"avif",
			"bmp",
			"gif",
			"jpeg",
			"png",
			"svg+xml",
			"webp",
			"x-icon"
		].map((type) => `image/${type}`));
	}
	static get supportedTypesStr() {
		return shadow$1(this, "supportedTypesStr", this.supportedTypes.join(","));
	}
	static isHandlingMimeForPasting(mime) {
		return this.supportedTypes.includes(mime);
	}
	static paste(item, parent) {
		parent.pasteEditor(AnnotationEditorType$1.STAMP, { bitmapFile: item.getAsFile() });
	}
	altTextFinish() {
		if (this._uiManager.useNewAltTextFlow) this.div.hidden = false;
		super.altTextFinish();
	}
	get telemetryFinalData() {
		return {
			type: "stamp",
			hasAltText: !!this.altTextData?.altText
		};
	}
	static computeTelemetryFinalData(data) {
		const hasAltTextStats = data.get("hasAltText");
		return {
			hasAltText: hasAltTextStats.get(true) ?? 0,
			hasNoAltText: hasAltTextStats.get(false) ?? 0
		};
	}
	#getBitmapFetched(data, fromId = false) {
		if (!data) {
			this.remove();
			return;
		}
		this.#bitmap = data.bitmap;
		if (!fromId) {
			this.#bitmapId = data.id;
			this.#isSvg = data.isSvg;
		}
		if (data.file) this.#bitmapFileName = data.file.name;
		this.#createCanvas();
	}
	#getBitmapDone() {
		this.#bitmapPromise = null;
		this._uiManager.enableWaiting(false);
		if (!this.#canvas) return;
		if (this._uiManager.useNewAltTextWhenAddingImage && this._uiManager.useNewAltTextFlow && this.#bitmap) {
			this._editToolbar.hide();
			this._uiManager.editAltText(this, true);
			return;
		}
		if (!this._uiManager.useNewAltTextWhenAddingImage && this._uiManager.useNewAltTextFlow && this.#bitmap) {
			this._reportTelemetry({
				action: "pdfjs.image.image_added",
				data: {
					alt_text_modal: false,
					alt_text_type: "empty"
				}
			});
			try {
				this.mlGuessAltText();
			} catch {}
		}
		this.div.focus();
	}
	async mlGuessAltText(imageData = null, updateAltTextData = true) {
		if (this.hasAltTextData()) return null;
		const { mlManager } = this._uiManager;
		if (!mlManager) throw new Error("No ML.");
		if (!await mlManager.isEnabledFor("altText")) throw new Error("ML isn't enabled for alt text.");
		const { data, width, height } = imageData || this.copyCanvas(null, null, true).imageData;
		const response = await mlManager.guess({
			name: "altText",
			request: {
				data,
				width,
				height,
				channels: data.length / (width * height)
			}
		});
		if (!response) throw new Error("No response from the AI service.");
		if (response.error) throw new Error("Error from the AI service.");
		if (response.cancel) return null;
		if (!response.output) throw new Error("No valid response from the AI service.");
		const altText = response.output;
		await this.setGuessedAltText(altText);
		if (updateAltTextData && !this.hasAltTextData()) this.altTextData = {
			alt: altText,
			decorative: false
		};
		return altText;
	}
	#getBitmap() {
		if (this.#bitmapId) {
			this._uiManager.enableWaiting(true);
			this._uiManager.imageManager.getFromId(this.#bitmapId).then((data) => this.#getBitmapFetched(data, true)).finally(() => this.#getBitmapDone());
			return;
		}
		if (this.#bitmapUrl) {
			const url = this.#bitmapUrl;
			this.#bitmapUrl = null;
			this._uiManager.enableWaiting(true);
			this.#bitmapPromise = this._uiManager.imageManager.getFromUrl(url).then((data) => this.#getBitmapFetched(data)).finally(() => this.#getBitmapDone());
			return;
		}
		if (this.#bitmapFile) {
			const file = this.#bitmapFile;
			this.#bitmapFile = null;
			this._uiManager.enableWaiting(true);
			this.#bitmapPromise = this._uiManager.imageManager.getFromFile(file).then((data) => this.#getBitmapFetched(data)).finally(() => this.#getBitmapDone());
			return;
		}
		const input = document.createElement("input");
		input.type = "file";
		input.accept = StampEditor.supportedTypesStr;
		const signal = this._uiManager._signal;
		this.#bitmapPromise = new Promise((resolve) => {
			input.addEventListener("change", async () => {
				if (!input.files || input.files.length === 0) this.remove();
				else {
					this._uiManager.enableWaiting(true);
					const data = await this._uiManager.imageManager.getFromFile(input.files[0]);
					this._reportTelemetry({
						action: "pdfjs.image.image_selected",
						data: { alt_text_modal: this._uiManager.useNewAltTextFlow }
					});
					this.#getBitmapFetched(data);
				}
				resolve();
			}, { signal });
			input.addEventListener("cancel", () => {
				this.remove();
				resolve();
			}, { signal });
		}).finally(() => this.#getBitmapDone());
		input.click();
	}
	remove() {
		if (this.#bitmapId) {
			this.#bitmap = null;
			this._uiManager.imageManager.deleteId(this.#bitmapId);
			this.#canvas?.remove();
			this.#canvas = null;
			if (this.#resizeTimeoutId) {
				clearTimeout(this.#resizeTimeoutId);
				this.#resizeTimeoutId = null;
			}
		}
		super.remove();
	}
	rebuild() {
		if (!this.parent) {
			if (this.#bitmapId) this.#getBitmap();
			return;
		}
		super.rebuild();
		if (this.div === null) return;
		if (this.#bitmapId && this.#canvas === null) this.#getBitmap();
		if (!this.isAttachedToDOM) this.parent.add(this);
	}
	onceAdded(focus) {
		this._isDraggable = true;
		if (focus) this.div.focus();
	}
	isEmpty() {
		return !(this.#bitmapPromise || this.#bitmap || this.#bitmapUrl || this.#bitmapFile || this.#bitmapId);
	}
	get isResizable() {
		return true;
	}
	render() {
		if (this.div) return this.div;
		let baseX, baseY;
		if (this.width) {
			baseX = this.x;
			baseY = this.y;
		}
		super.render();
		this.div.hidden = true;
		this.div.setAttribute("role", "figure");
		this.addAltTextButton();
		if (this.#bitmap) this.#createCanvas();
		else this.#getBitmap();
		if (this.width && !this.annotationElementId) {
			const [parentWidth, parentHeight] = this.parentDimensions;
			this.setAt(baseX * parentWidth, baseY * parentHeight, this.width * parentWidth, this.height * parentHeight);
		}
		this._uiManager.addShouldRescale(this);
		return this.div;
	}
	_onResized() {
		this.onScaleChanging();
	}
	onScaleChanging() {
		if (!this.parent) return;
		if (this.#resizeTimeoutId !== null) clearTimeout(this.#resizeTimeoutId);
		const TIME_TO_WAIT = 200;
		this.#resizeTimeoutId = setTimeout(() => {
			this.#resizeTimeoutId = null;
			this.#drawBitmap();
		}, TIME_TO_WAIT);
	}
	#createCanvas() {
		const { div } = this;
		let { width, height } = this.#bitmap;
		const [pageWidth, pageHeight] = this.pageDimensions;
		const MAX_RATIO = .75;
		if (this.width) {
			width = this.width * pageWidth;
			height = this.height * pageHeight;
		} else if (width > MAX_RATIO * pageWidth || height > MAX_RATIO * pageHeight) {
			const factor = Math.min(MAX_RATIO * pageWidth / width, MAX_RATIO * pageHeight / height);
			width *= factor;
			height *= factor;
		}
		const [parentWidth, parentHeight] = this.parentDimensions;
		this.setDims(width * parentWidth / pageWidth, height * parentHeight / pageHeight);
		this._uiManager.enableWaiting(false);
		const canvas = this.#canvas = document.createElement("canvas");
		canvas.setAttribute("role", "img");
		this.addContainer(canvas);
		this.width = width / pageWidth;
		this.height = height / pageHeight;
		if (this._initialOptions?.isCentered) this.center();
		else this.fixAndSetPosition();
		this._initialOptions = null;
		if (!this._uiManager.useNewAltTextWhenAddingImage || !this._uiManager.useNewAltTextFlow || this.annotationElementId) div.hidden = false;
		this.#drawBitmap();
		if (!this.#hasBeenAddedInUndoStack) {
			this.parent.addUndoableEditor(this);
			this.#hasBeenAddedInUndoStack = true;
		}
		this._reportTelemetry({ action: "inserted_image" });
		if (this.#bitmapFileName) canvas.setAttribute("aria-label", this.#bitmapFileName);
	}
	copyCanvas(maxDataDimension, maxPreviewDimension, createImageData = false) {
		if (!maxDataDimension) maxDataDimension = 224;
		const { width: bitmapWidth, height: bitmapHeight } = this.#bitmap;
		const outputScale = new OutputScale$1();
		let bitmap = this.#bitmap;
		let width = bitmapWidth, height = bitmapHeight;
		let canvas = null;
		if (maxPreviewDimension) {
			if (bitmapWidth > maxPreviewDimension || bitmapHeight > maxPreviewDimension) {
				const ratio = Math.min(maxPreviewDimension / bitmapWidth, maxPreviewDimension / bitmapHeight);
				width = Math.floor(bitmapWidth * ratio);
				height = Math.floor(bitmapHeight * ratio);
			}
			canvas = document.createElement("canvas");
			const scaledWidth = canvas.width = Math.ceil(width * outputScale.sx);
			const scaledHeight = canvas.height = Math.ceil(height * outputScale.sy);
			if (!this.#isSvg) bitmap = this.#scaleBitmap(scaledWidth, scaledHeight);
			const ctx = canvas.getContext("2d");
			ctx.filter = this._uiManager.hcmFilter;
			let white = "white", black = "#cfcfd8";
			if (this._uiManager.hcmFilter !== "none") black = "black";
			else if (window.matchMedia?.("(prefers-color-scheme: dark)").matches) {
				white = "#8f8f9d";
				black = "#42414d";
			}
			const boxDim = 15;
			const boxDimWidth = boxDim * outputScale.sx;
			const boxDimHeight = boxDim * outputScale.sy;
			const pattern = new OffscreenCanvas(boxDimWidth * 2, boxDimHeight * 2);
			const patternCtx = pattern.getContext("2d");
			patternCtx.fillStyle = white;
			patternCtx.fillRect(0, 0, boxDimWidth * 2, boxDimHeight * 2);
			patternCtx.fillStyle = black;
			patternCtx.fillRect(0, 0, boxDimWidth, boxDimHeight);
			patternCtx.fillRect(boxDimWidth, boxDimHeight, boxDimWidth, boxDimHeight);
			ctx.fillStyle = ctx.createPattern(pattern, "repeat");
			ctx.fillRect(0, 0, scaledWidth, scaledHeight);
			ctx.drawImage(bitmap, 0, 0, bitmap.width, bitmap.height, 0, 0, scaledWidth, scaledHeight);
		}
		let imageData = null;
		if (createImageData) {
			let dataWidth, dataHeight;
			if (outputScale.symmetric && bitmap.width < maxDataDimension && bitmap.height < maxDataDimension) {
				dataWidth = bitmap.width;
				dataHeight = bitmap.height;
			} else {
				bitmap = this.#bitmap;
				if (bitmapWidth > maxDataDimension || bitmapHeight > maxDataDimension) {
					const ratio = Math.min(maxDataDimension / bitmapWidth, maxDataDimension / bitmapHeight);
					dataWidth = Math.floor(bitmapWidth * ratio);
					dataHeight = Math.floor(bitmapHeight * ratio);
					if (!this.#isSvg) bitmap = this.#scaleBitmap(dataWidth, dataHeight);
				}
			}
			const offscreenCtx = new OffscreenCanvas(dataWidth, dataHeight).getContext("2d", { willReadFrequently: true });
			offscreenCtx.drawImage(bitmap, 0, 0, bitmap.width, bitmap.height, 0, 0, dataWidth, dataHeight);
			imageData = {
				width: dataWidth,
				height: dataHeight,
				data: offscreenCtx.getImageData(0, 0, dataWidth, dataHeight).data
			};
		}
		return {
			canvas,
			width,
			height,
			imageData
		};
	}
	#scaleBitmap(width, height) {
		const { width: bitmapWidth, height: bitmapHeight } = this.#bitmap;
		let newWidth = bitmapWidth;
		let newHeight = bitmapHeight;
		let bitmap = this.#bitmap;
		while (newWidth > 2 * width || newHeight > 2 * height) {
			const prevWidth = newWidth;
			const prevHeight = newHeight;
			if (newWidth > 2 * width) newWidth = newWidth >= 16384 ? Math.floor(newWidth / 2) - 1 : Math.ceil(newWidth / 2);
			if (newHeight > 2 * height) newHeight = newHeight >= 16384 ? Math.floor(newHeight / 2) - 1 : Math.ceil(newHeight / 2);
			const offscreen = new OffscreenCanvas(newWidth, newHeight);
			offscreen.getContext("2d").drawImage(bitmap, 0, 0, prevWidth, prevHeight, 0, 0, newWidth, newHeight);
			bitmap = offscreen.transferToImageBitmap();
		}
		return bitmap;
	}
	#drawBitmap() {
		const [parentWidth, parentHeight] = this.parentDimensions;
		const { width, height } = this;
		const outputScale = new OutputScale$1();
		const scaledWidth = Math.ceil(width * parentWidth * outputScale.sx);
		const scaledHeight = Math.ceil(height * parentHeight * outputScale.sy);
		const canvas = this.#canvas;
		if (!canvas || canvas.width === scaledWidth && canvas.height === scaledHeight) return;
		canvas.width = scaledWidth;
		canvas.height = scaledHeight;
		const bitmap = this.#isSvg ? this.#bitmap : this.#scaleBitmap(scaledWidth, scaledHeight);
		const ctx = canvas.getContext("2d");
		ctx.filter = this._uiManager.hcmFilter;
		ctx.drawImage(bitmap, 0, 0, bitmap.width, bitmap.height, 0, 0, scaledWidth, scaledHeight);
	}
	getImageForAltText() {
		return this.#canvas;
	}
	#serializeBitmap(toUrl) {
		if (toUrl) {
			if (this.#isSvg) {
				const url = this._uiManager.imageManager.getSvgUrl(this.#bitmapId);
				if (url) return url;
			}
			const canvas = document.createElement("canvas");
			({width: canvas.width, height: canvas.height} = this.#bitmap);
			canvas.getContext("2d").drawImage(this.#bitmap, 0, 0);
			return canvas.toDataURL();
		}
		if (this.#isSvg) {
			const [pageWidth, pageHeight] = this.pageDimensions;
			const width = Math.round(this.width * pageWidth * PixelsPerInch$1.PDF_TO_CSS_UNITS);
			const height = Math.round(this.height * pageHeight * PixelsPerInch$1.PDF_TO_CSS_UNITS);
			const offscreen = new OffscreenCanvas(width, height);
			offscreen.getContext("2d").drawImage(this.#bitmap, 0, 0, this.#bitmap.width, this.#bitmap.height, 0, 0, width, height);
			return offscreen.transferToImageBitmap();
		}
		return structuredClone(this.#bitmap);
	}
	static async deserialize(data, parent, uiManager) {
		let initialData = null;
		if (data instanceof StampAnnotationElement) {
			const { data: { rect, rotation, id, structParent, popupRef }, container, parent: { page: { pageNumber } } } = data;
			const canvas = container.querySelector("canvas");
			const imageData = uiManager.imageManager.getFromCanvas(container.id, canvas);
			canvas.remove();
			const altText = (await parent._structTree.getAriaAttributes(`${AnnotationPrefix}${id}`))?.get("aria-label") || "";
			initialData = data = {
				annotationType: AnnotationEditorType$1.STAMP,
				bitmapId: imageData.id,
				bitmap: imageData.bitmap,
				pageIndex: pageNumber - 1,
				rect: rect.slice(0),
				rotation,
				id,
				deleted: false,
				accessibilityData: {
					decorative: false,
					altText
				},
				isSvg: false,
				structParent,
				popupRef
			};
		}
		const editor = await super.deserialize(data, parent, uiManager);
		const { rect, bitmap, bitmapUrl, bitmapId, isSvg, accessibilityData } = data;
		if (bitmapId && uiManager.imageManager.isValidId(bitmapId)) {
			editor.#bitmapId = bitmapId;
			if (bitmap) editor.#bitmap = bitmap;
		} else editor.#bitmapUrl = bitmapUrl;
		editor.#isSvg = isSvg;
		const [parentWidth, parentHeight] = editor.pageDimensions;
		editor.width = (rect[2] - rect[0]) / parentWidth;
		editor.height = (rect[3] - rect[1]) / parentHeight;
		editor.annotationElementId = data.id || null;
		if (accessibilityData) editor.altTextData = accessibilityData;
		editor._initialData = initialData;
		editor.#hasBeenAddedInUndoStack = !!initialData;
		return editor;
	}
	serialize(isForCopying = false, context = null) {
		if (this.isEmpty()) return null;
		if (this.deleted) return this.serializeDeleted();
		const serialized = {
			annotationType: AnnotationEditorType$1.STAMP,
			bitmapId: this.#bitmapId,
			pageIndex: this.pageIndex,
			rect: this.getRect(0, 0),
			rotation: this.rotation,
			isSvg: this.#isSvg,
			structTreeParentId: this._structTreeParentId
		};
		if (isForCopying) {
			serialized.bitmapUrl = this.#serializeBitmap(true);
			serialized.accessibilityData = this.serializeAltText(true);
			return serialized;
		}
		const { decorative, altText } = this.serializeAltText(false);
		if (!decorative && altText) serialized.accessibilityData = {
			type: "Figure",
			alt: altText
		};
		if (this.annotationElementId) {
			const changes = this.#hasElementChanged(serialized);
			if (changes.isSame) return null;
			if (changes.isSameAltText) delete serialized.accessibilityData;
			else serialized.accessibilityData.structParent = this._initialData.structParent ?? -1;
		}
		serialized.id = this.annotationElementId;
		if (context === null) return serialized;
		context.stamps ||= /* @__PURE__ */ new Map();
		const area = this.#isSvg ? (serialized.rect[2] - serialized.rect[0]) * (serialized.rect[3] - serialized.rect[1]) : null;
		if (!context.stamps.has(this.#bitmapId)) {
			context.stamps.set(this.#bitmapId, {
				area,
				serialized
			});
			serialized.bitmap = this.#serializeBitmap(false);
		} else if (this.#isSvg) {
			const prevData = context.stamps.get(this.#bitmapId);
			if (area > prevData.area) {
				prevData.area = area;
				prevData.serialized.bitmap.close();
				prevData.serialized.bitmap = this.#serializeBitmap(false);
			}
		}
		return serialized;
	}
	#hasElementChanged(serialized) {
		const { pageIndex, accessibilityData: { altText } } = this._initialData;
		const isSamePageIndex = serialized.pageIndex === pageIndex;
		const isSameAltText = (serialized.accessibilityData?.alt || "") === altText;
		return {
			isSame: !this._hasBeenMoved && !this._hasBeenResized && isSamePageIndex && isSameAltText,
			isSameAltText
		};
	}
	renderAnnotationElement(annotation) {
		annotation.updateEdited({ rect: this.getRect(0, 0) });
		return null;
	}
};
var AnnotationEditorLayer$1 = class AnnotationEditorLayer$1 {
	#accessibilityManager;
	#allowClick = false;
	#annotationLayer = null;
	#clickAC = null;
	#editorFocusTimeoutId = null;
	#editors = /* @__PURE__ */ new Map();
	#hadPointerDown = false;
	#isDisabling = false;
	#isEnabling = false;
	#drawingAC = null;
	#focusedElement = null;
	#textLayer = null;
	#textSelectionAC = null;
	#uiManager;
	static _initialized = false;
	static #editorTypes = new Map([
		FreeTextEditor,
		InkEditor,
		StampEditor,
		HighlightEditor
	].map((type) => [type._editorType, type]));
	constructor({ uiManager, pageIndex, div, structTreeLayer, accessibilityManager, annotationLayer, drawLayer, textLayer, viewport, l10n }) {
		const editorTypes = [...AnnotationEditorLayer$1.#editorTypes.values()];
		if (!AnnotationEditorLayer$1._initialized) {
			AnnotationEditorLayer$1._initialized = true;
			for (const editorType of editorTypes) editorType.initialize(l10n, uiManager);
		}
		uiManager.registerEditorTypes(editorTypes);
		this.#uiManager = uiManager;
		this.pageIndex = pageIndex;
		this.div = div;
		this.#accessibilityManager = accessibilityManager;
		this.#annotationLayer = annotationLayer;
		this.viewport = viewport;
		this.#textLayer = textLayer;
		this.drawLayer = drawLayer;
		this._structTree = structTreeLayer;
		this.#uiManager.addLayer(this);
	}
	get isEmpty() {
		return this.#editors.size === 0;
	}
	get isInvisible() {
		return this.isEmpty && this.#uiManager.getMode() === AnnotationEditorType$1.NONE;
	}
	updateToolbar(mode) {
		this.#uiManager.updateToolbar(mode);
	}
	updateMode(mode = this.#uiManager.getMode()) {
		this.#cleanup();
		switch (mode) {
			case AnnotationEditorType$1.NONE:
				this.disableTextSelection();
				this.togglePointerEvents(false);
				this.toggleAnnotationLayerPointerEvents(true);
				this.disableClick();
				return;
			case AnnotationEditorType$1.INK:
				this.disableTextSelection();
				this.togglePointerEvents(true);
				this.enableClick();
				break;
			case AnnotationEditorType$1.HIGHLIGHT:
				this.enableTextSelection();
				this.togglePointerEvents(false);
				this.disableClick();
				break;
			default:
				this.disableTextSelection();
				this.togglePointerEvents(true);
				this.enableClick();
		}
		this.toggleAnnotationLayerPointerEvents(false);
		const { classList } = this.div;
		for (const editorType of AnnotationEditorLayer$1.#editorTypes.values()) classList.toggle(`${editorType._type}Editing`, mode === editorType._editorType);
		this.div.hidden = false;
	}
	hasTextLayer(textLayer) {
		return textLayer === this.#textLayer?.div;
	}
	setEditingState(isEditing) {
		this.#uiManager.setEditingState(isEditing);
	}
	addCommands(params) {
		this.#uiManager.addCommands(params);
	}
	cleanUndoStack(type) {
		this.#uiManager.cleanUndoStack(type);
	}
	toggleDrawing(enabled = false) {
		this.div.classList.toggle("drawing", !enabled);
	}
	togglePointerEvents(enabled = false) {
		this.div.classList.toggle("disabled", !enabled);
	}
	toggleAnnotationLayerPointerEvents(enabled = false) {
		this.#annotationLayer?.div.classList.toggle("disabled", !enabled);
	}
	async enable() {
		this.#isEnabling = true;
		this.div.tabIndex = 0;
		this.togglePointerEvents(true);
		const annotationElementIds = /* @__PURE__ */ new Set();
		for (const editor of this.#editors.values()) {
			editor.enableEditing();
			editor.show(true);
			if (editor.annotationElementId) {
				this.#uiManager.removeChangedExistingAnnotation(editor);
				annotationElementIds.add(editor.annotationElementId);
			}
		}
		if (!this.#annotationLayer) {
			this.#isEnabling = false;
			return;
		}
		const editables = this.#annotationLayer.getEditableAnnotations();
		for (const editable of editables) {
			editable.hide();
			if (this.#uiManager.isDeletedAnnotationElement(editable.data.id)) continue;
			if (annotationElementIds.has(editable.data.id)) continue;
			const editor = await this.deserialize(editable);
			if (!editor) continue;
			this.addOrRebuild(editor);
			editor.enableEditing();
		}
		this.#isEnabling = false;
	}
	disable() {
		this.#isDisabling = true;
		this.div.tabIndex = -1;
		this.togglePointerEvents(false);
		const changedAnnotations = /* @__PURE__ */ new Map();
		const resetAnnotations = /* @__PURE__ */ new Map();
		for (const editor of this.#editors.values()) {
			editor.disableEditing();
			if (!editor.annotationElementId) continue;
			if (editor.serialize() !== null) {
				changedAnnotations.set(editor.annotationElementId, editor);
				continue;
			} else resetAnnotations.set(editor.annotationElementId, editor);
			this.getEditableAnnotation(editor.annotationElementId)?.show();
			editor.remove();
		}
		if (this.#annotationLayer) {
			const editables = this.#annotationLayer.getEditableAnnotations();
			for (const editable of editables) {
				const { id } = editable.data;
				if (this.#uiManager.isDeletedAnnotationElement(id)) continue;
				let editor = resetAnnotations.get(id);
				if (editor) {
					editor.resetAnnotationElement(editable);
					editor.show(false);
					editable.show();
					continue;
				}
				editor = changedAnnotations.get(id);
				if (editor) {
					this.#uiManager.addChangedExistingAnnotation(editor);
					if (editor.renderAnnotationElement(editable)) editor.show(false);
				}
				editable.show();
			}
		}
		this.#cleanup();
		if (this.isEmpty) this.div.hidden = true;
		const { classList } = this.div;
		for (const editorType of AnnotationEditorLayer$1.#editorTypes.values()) classList.remove(`${editorType._type}Editing`);
		this.disableTextSelection();
		this.toggleAnnotationLayerPointerEvents(true);
		this.#isDisabling = false;
	}
	getEditableAnnotation(id) {
		return this.#annotationLayer?.getEditableAnnotation(id) || null;
	}
	setActiveEditor(editor) {
		if (this.#uiManager.getActive() === editor) return;
		this.#uiManager.setActiveEditor(editor);
	}
	enableTextSelection() {
		this.div.tabIndex = -1;
		if (this.#textLayer?.div && !this.#textSelectionAC) {
			this.#textSelectionAC = new AbortController();
			const signal = this.#uiManager.combinedSignal(this.#textSelectionAC);
			this.#textLayer.div.addEventListener("pointerdown", this.#textLayerPointerDown.bind(this), { signal });
			this.#textLayer.div.classList.add("highlighting");
		}
	}
	disableTextSelection() {
		this.div.tabIndex = 0;
		if (this.#textLayer?.div && this.#textSelectionAC) {
			this.#textSelectionAC.abort();
			this.#textSelectionAC = null;
			this.#textLayer.div.classList.remove("highlighting");
		}
	}
	#textLayerPointerDown(event) {
		this.#uiManager.unselectAll();
		const { target } = event;
		if (target === this.#textLayer.div || (target.getAttribute("role") === "img" || target.classList.contains("endOfContent")) && this.#textLayer.div.contains(target)) {
			const { isMac } = util_FeatureTest.platform;
			if (event.button !== 0 || event.ctrlKey && isMac) return;
			this.#uiManager.showAllEditors("highlight", true, true);
			this.#textLayer.div.classList.add("free");
			this.toggleDrawing();
			HighlightEditor.startHighlighting(this, this.#uiManager.direction === "ltr", {
				target: this.#textLayer.div,
				x: event.x,
				y: event.y
			});
			this.#textLayer.div.addEventListener("pointerup", () => {
				this.#textLayer.div.classList.remove("free");
				this.toggleDrawing(true);
			}, {
				once: true,
				signal: this.#uiManager._signal
			});
			event.preventDefault();
		}
	}
	enableClick() {
		if (this.#clickAC) return;
		this.#clickAC = new AbortController();
		const signal = this.#uiManager.combinedSignal(this.#clickAC);
		this.div.addEventListener("pointerdown", this.pointerdown.bind(this), { signal });
		const pointerup = this.pointerup.bind(this);
		this.div.addEventListener("pointerup", pointerup, { signal });
		this.div.addEventListener("pointercancel", pointerup, { signal });
	}
	disableClick() {
		this.#clickAC?.abort();
		this.#clickAC = null;
	}
	attach(editor) {
		this.#editors.set(editor.id, editor);
		const { annotationElementId } = editor;
		if (annotationElementId && this.#uiManager.isDeletedAnnotationElement(annotationElementId)) this.#uiManager.removeDeletedAnnotationElement(editor);
	}
	detach(editor) {
		this.#editors.delete(editor.id);
		this.#accessibilityManager?.removePointerInTextLayer(editor.contentDiv);
		if (!this.#isDisabling && editor.annotationElementId) this.#uiManager.addDeletedAnnotationElement(editor);
	}
	remove(editor) {
		this.detach(editor);
		this.#uiManager.removeEditor(editor);
		editor.div.remove();
		editor.isAttachedToDOM = false;
	}
	changeParent(editor) {
		if (editor.parent === this) return;
		if (editor.parent && editor.annotationElementId) {
			this.#uiManager.addDeletedAnnotationElement(editor.annotationElementId);
			AnnotationEditor.deleteAnnotationElement(editor);
			editor.annotationElementId = null;
		}
		this.attach(editor);
		editor.parent?.detach(editor);
		editor.setParent(this);
		if (editor.div && editor.isAttachedToDOM) {
			editor.div.remove();
			this.div.append(editor.div);
		}
	}
	add(editor) {
		if (editor.parent === this && editor.isAttachedToDOM) return;
		this.changeParent(editor);
		this.#uiManager.addEditor(editor);
		this.attach(editor);
		if (!editor.isAttachedToDOM) {
			const div = editor.render();
			this.div.append(div);
			editor.isAttachedToDOM = true;
		}
		editor.fixAndSetPosition();
		editor.onceAdded(!this.#isEnabling);
		this.#uiManager.addToAnnotationStorage(editor);
		editor._reportTelemetry(editor.telemetryInitialData);
	}
	moveEditorInDOM(editor) {
		if (!editor.isAttachedToDOM) return;
		const { activeElement } = document;
		if (editor.div.contains(activeElement) && !this.#editorFocusTimeoutId) {
			editor._focusEventsAllowed = false;
			this.#editorFocusTimeoutId = setTimeout(() => {
				this.#editorFocusTimeoutId = null;
				if (!editor.div.contains(document.activeElement)) {
					editor.div.addEventListener("focusin", () => {
						editor._focusEventsAllowed = true;
					}, {
						once: true,
						signal: this.#uiManager._signal
					});
					activeElement.focus();
				} else editor._focusEventsAllowed = true;
			}, 0);
		}
		editor._structTreeParentId = this.#accessibilityManager?.moveElementInDOM(this.div, editor.div, editor.contentDiv, true);
	}
	addOrRebuild(editor) {
		if (editor.needsToBeRebuilt()) {
			editor.parent ||= this;
			editor.rebuild();
			editor.show();
		} else this.add(editor);
	}
	addUndoableEditor(editor) {
		const cmd = () => editor._uiManager.rebuild(editor);
		const undo = () => {
			editor.remove();
		};
		this.addCommands({
			cmd,
			undo,
			mustExec: false
		});
	}
	getNextId() {
		return this.#uiManager.getId();
	}
	get #currentEditorType() {
		return AnnotationEditorLayer$1.#editorTypes.get(this.#uiManager.getMode());
	}
	combinedSignal(ac) {
		return this.#uiManager.combinedSignal(ac);
	}
	#createNewEditor(params) {
		const editorType = this.#currentEditorType;
		return editorType ? new editorType.prototype.constructor(params) : null;
	}
	canCreateNewEmptyEditor() {
		return this.#currentEditorType?.canCreateNewEmptyEditor();
	}
	pasteEditor(mode, params) {
		this.#uiManager.updateToolbar(mode);
		this.#uiManager.updateMode(mode);
		const { offsetX, offsetY } = this.#getCenterPoint();
		const id = this.getNextId();
		const editor = this.#createNewEditor({
			parent: this,
			id,
			x: offsetX,
			y: offsetY,
			uiManager: this.#uiManager,
			isCentered: true,
			...params
		});
		if (editor) this.add(editor);
	}
	async deserialize(data) {
		return await AnnotationEditorLayer$1.#editorTypes.get(data.annotationType ?? data.annotationEditorType)?.deserialize(data, this, this.#uiManager) || null;
	}
	createAndAddNewEditor(event, isCentered, data = {}) {
		const id = this.getNextId();
		const editor = this.#createNewEditor({
			parent: this,
			id,
			x: event.offsetX,
			y: event.offsetY,
			uiManager: this.#uiManager,
			isCentered,
			...data
		});
		if (editor) this.add(editor);
		return editor;
	}
	#getCenterPoint() {
		const { x, y, width, height } = this.div.getBoundingClientRect();
		const tlX = Math.max(0, x);
		const tlY = Math.max(0, y);
		const brX = Math.min(window.innerWidth, x + width);
		const brY = Math.min(window.innerHeight, y + height);
		const centerX = (tlX + brX) / 2 - x;
		const centerY = (tlY + brY) / 2 - y;
		const [offsetX, offsetY] = this.viewport.rotation % 180 === 0 ? [centerX, centerY] : [centerY, centerX];
		return {
			offsetX,
			offsetY
		};
	}
	addNewEditor() {
		this.createAndAddNewEditor(this.#getCenterPoint(), true);
	}
	setSelected(editor) {
		this.#uiManager.setSelected(editor);
	}
	toggleSelected(editor) {
		this.#uiManager.toggleSelected(editor);
	}
	unselect(editor) {
		this.#uiManager.unselect(editor);
	}
	pointerup(event) {
		const { isMac } = util_FeatureTest.platform;
		if (event.button !== 0 || event.ctrlKey && isMac) return;
		if (event.target !== this.div) return;
		if (!this.#hadPointerDown) return;
		this.#hadPointerDown = false;
		if (this.#currentEditorType?.isDrawer && this.#currentEditorType.supportMultipleDrawings) return;
		if (!this.#allowClick) {
			this.#allowClick = true;
			return;
		}
		if (this.#uiManager.getMode() === AnnotationEditorType$1.STAMP) {
			this.#uiManager.unselectAll();
			return;
		}
		this.createAndAddNewEditor(event, false);
	}
	pointerdown(event) {
		if (this.#uiManager.getMode() === AnnotationEditorType$1.HIGHLIGHT) this.enableTextSelection();
		if (this.#hadPointerDown) {
			this.#hadPointerDown = false;
			return;
		}
		const { isMac } = util_FeatureTest.platform;
		if (event.button !== 0 || event.ctrlKey && isMac) return;
		if (event.target !== this.div) return;
		this.#hadPointerDown = true;
		if (this.#currentEditorType?.isDrawer) {
			this.startDrawingSession(event);
			return;
		}
		const editor = this.#uiManager.getActive();
		this.#allowClick = !editor || editor.isEmpty();
	}
	startDrawingSession(event) {
		this.div.focus();
		if (this.#drawingAC) {
			this.#currentEditorType.startDrawing(this, this.#uiManager, false, event);
			return;
		}
		this.#uiManager.setCurrentDrawingSession(this);
		this.#drawingAC = new AbortController();
		const signal = this.#uiManager.combinedSignal(this.#drawingAC);
		this.div.addEventListener("blur", ({ relatedTarget }) => {
			if (relatedTarget && !this.div.contains(relatedTarget)) {
				this.#focusedElement = null;
				this.commitOrRemove();
			}
		}, { signal });
		this.#currentEditorType.startDrawing(this, this.#uiManager, false, event);
	}
	pause(on) {
		if (on) {
			const { activeElement } = document;
			if (this.div.contains(activeElement)) this.#focusedElement = activeElement;
			return;
		}
		if (this.#focusedElement) setTimeout(() => {
			this.#focusedElement?.focus();
			this.#focusedElement = null;
		}, 0);
	}
	endDrawingSession(isAborted = false) {
		if (!this.#drawingAC) return null;
		this.#uiManager.setCurrentDrawingSession(null);
		this.#drawingAC.abort();
		this.#drawingAC = null;
		this.#focusedElement = null;
		return this.#currentEditorType.endDrawing(isAborted);
	}
	findNewParent(editor, x, y) {
		const layer = this.#uiManager.findParent(x, y);
		if (layer === null || layer === this) return false;
		layer.changeParent(editor);
		return true;
	}
	commitOrRemove() {
		if (this.#drawingAC) {
			this.endDrawingSession();
			return true;
		}
		return false;
	}
	onScaleChanging() {
		if (!this.#drawingAC) return;
		this.#currentEditorType.onScaleChangingWhenDrawing(this);
	}
	destroy() {
		this.commitOrRemove();
		if (this.#uiManager.getActive()?.parent === this) {
			this.#uiManager.commitOrRemove();
			this.#uiManager.setActiveEditor(null);
		}
		if (this.#editorFocusTimeoutId) {
			clearTimeout(this.#editorFocusTimeoutId);
			this.#editorFocusTimeoutId = null;
		}
		for (const editor of this.#editors.values()) {
			this.#accessibilityManager?.removePointerInTextLayer(editor.contentDiv);
			editor.setParent(null);
			editor.isAttachedToDOM = false;
			editor.div.remove();
		}
		this.div = null;
		this.#editors.clear();
		this.#uiManager.removeLayer(this);
	}
	#cleanup() {
		for (const editor of this.#editors.values()) if (editor.isEmpty()) editor.remove();
	}
	render({ viewport }) {
		this.viewport = viewport;
		setLayerDimensions$1(this.div, viewport);
		for (const editor of this.#uiManager.getEditors(this.pageIndex)) {
			this.add(editor);
			editor.rebuild();
		}
		this.updateMode();
	}
	update({ viewport }) {
		this.#uiManager.commitOrRemove();
		this.#cleanup();
		const oldRotation = this.viewport.rotation;
		const rotation = viewport.rotation;
		this.viewport = viewport;
		setLayerDimensions$1(this.div, { rotation });
		if (oldRotation !== rotation) for (const editor of this.#editors.values()) editor.rotate(rotation);
	}
	get pageDimensions() {
		const { pageWidth, pageHeight } = this.viewport.rawDims;
		return [pageWidth, pageHeight];
	}
	get scale() {
		return this.#uiManager.viewParameters.realScale;
	}
};
var DrawLayer$1 = class DrawLayer$1 {
	#parent = null;
	#id = 0;
	#mapping = /* @__PURE__ */ new Map();
	#toUpdate = /* @__PURE__ */ new Map();
	constructor({ pageIndex }) {
		this.pageIndex = pageIndex;
	}
	setParent(parent) {
		if (!this.#parent) {
			this.#parent = parent;
			return;
		}
		if (this.#parent !== parent) {
			if (this.#mapping.size > 0) for (const root of this.#mapping.values()) {
				root.remove();
				parent.append(root);
			}
			this.#parent = parent;
		}
	}
	static get _svgFactory() {
		return shadow$1(this, "_svgFactory", new DOMSVGFactory$1());
	}
	static #setBox(element, [x, y, width, height]) {
		const { style } = element;
		style.top = `${100 * y}%`;
		style.left = `${100 * x}%`;
		style.width = `${100 * width}%`;
		style.height = `${100 * height}%`;
	}
	#createSVG() {
		const svg = DrawLayer$1._svgFactory.create(1, 1, true);
		this.#parent.append(svg);
		svg.setAttribute("aria-hidden", true);
		return svg;
	}
	#createClipPath(defs, pathId) {
		const clipPath = DrawLayer$1._svgFactory.createElement("clipPath");
		defs.append(clipPath);
		const clipPathId = `clip_${pathId}`;
		clipPath.setAttribute("id", clipPathId);
		clipPath.setAttribute("clipPathUnits", "objectBoundingBox");
		const clipPathUse = DrawLayer$1._svgFactory.createElement("use");
		clipPath.append(clipPathUse);
		clipPathUse.setAttribute("href", `#${pathId}`);
		clipPathUse.classList.add("clip");
		return clipPathId;
	}
	#updateProperties(element, properties) {
		for (const [key, value] of Object.entries(properties)) if (value === null) element.removeAttribute(key);
		else element.setAttribute(key, value);
	}
	draw(properties, isPathUpdatable = false, hasClip = false) {
		const id = this.#id++;
		const root = this.#createSVG();
		const defs = DrawLayer$1._svgFactory.createElement("defs");
		root.append(defs);
		const path = DrawLayer$1._svgFactory.createElement("path");
		defs.append(path);
		const pathId = `path_p${this.pageIndex}_${id}`;
		path.setAttribute("id", pathId);
		path.setAttribute("vector-effect", "non-scaling-stroke");
		if (isPathUpdatable) this.#toUpdate.set(id, path);
		const clipPathId = hasClip ? this.#createClipPath(defs, pathId) : null;
		const use = DrawLayer$1._svgFactory.createElement("use");
		root.append(use);
		use.setAttribute("href", `#${pathId}`);
		this.updateProperties(root, properties);
		this.#mapping.set(id, root);
		return {
			id,
			clipPathId: `url(#${clipPathId})`
		};
	}
	drawOutline(properties, mustRemoveSelfIntersections) {
		const id = this.#id++;
		const root = this.#createSVG();
		const defs = DrawLayer$1._svgFactory.createElement("defs");
		root.append(defs);
		const path = DrawLayer$1._svgFactory.createElement("path");
		defs.append(path);
		const pathId = `path_p${this.pageIndex}_${id}`;
		path.setAttribute("id", pathId);
		path.setAttribute("vector-effect", "non-scaling-stroke");
		let maskId;
		if (mustRemoveSelfIntersections) {
			const mask = DrawLayer$1._svgFactory.createElement("mask");
			defs.append(mask);
			maskId = `mask_p${this.pageIndex}_${id}`;
			mask.setAttribute("id", maskId);
			mask.setAttribute("maskUnits", "objectBoundingBox");
			const rect = DrawLayer$1._svgFactory.createElement("rect");
			mask.append(rect);
			rect.setAttribute("width", "1");
			rect.setAttribute("height", "1");
			rect.setAttribute("fill", "white");
			const use = DrawLayer$1._svgFactory.createElement("use");
			mask.append(use);
			use.setAttribute("href", `#${pathId}`);
			use.setAttribute("stroke", "none");
			use.setAttribute("fill", "black");
			use.setAttribute("fill-rule", "nonzero");
			use.classList.add("mask");
		}
		const use1 = DrawLayer$1._svgFactory.createElement("use");
		root.append(use1);
		use1.setAttribute("href", `#${pathId}`);
		if (maskId) use1.setAttribute("mask", `url(#${maskId})`);
		const use2 = use1.cloneNode();
		root.append(use2);
		use1.classList.add("mainOutline");
		use2.classList.add("secondaryOutline");
		this.updateProperties(root, properties);
		this.#mapping.set(id, root);
		return id;
	}
	finalizeDraw(id, properties) {
		this.#toUpdate.delete(id);
		this.updateProperties(id, properties);
	}
	updateProperties(elementOrId, properties) {
		if (!properties) return;
		const { root, bbox, rootClass, path } = properties;
		const element = typeof elementOrId === "number" ? this.#mapping.get(elementOrId) : elementOrId;
		if (!element) return;
		if (root) this.#updateProperties(element, root);
		if (bbox) DrawLayer$1.#setBox(element, bbox);
		if (rootClass) {
			const { classList } = element;
			for (const [className, value] of Object.entries(rootClass)) classList.toggle(className, value);
		}
		if (path) {
			const pathElement = element.firstChild.firstChild;
			this.#updateProperties(pathElement, path);
		}
	}
	updateParent(id, layer) {
		if (layer === this) return;
		const root = this.#mapping.get(id);
		if (!root) return;
		layer.#parent.append(root);
		this.#mapping.delete(id);
		layer.#mapping.set(id, root);
	}
	remove(id) {
		this.#toUpdate.delete(id);
		if (this.#parent === null) return;
		this.#mapping.get(id).remove();
		this.#mapping.delete(id);
	}
	destroy() {
		this.#parent = null;
		for (const root of this.#mapping.values()) root.remove();
		this.#mapping.clear();
		this.#toUpdate.clear();
	}
};
globalThis.pdfjsTestingUtils = { HighlightOutliner };
var __webpack_exports__AbortException = __webpack_exports__$1.AbortException;
var __webpack_exports__AnnotationEditorLayer = __webpack_exports__$1.AnnotationEditorLayer;
var __webpack_exports__AnnotationEditorParamsType = __webpack_exports__$1.AnnotationEditorParamsType;
var __webpack_exports__AnnotationEditorType = __webpack_exports__$1.AnnotationEditorType;
var __webpack_exports__AnnotationEditorUIManager = __webpack_exports__$1.AnnotationEditorUIManager;
var __webpack_exports__AnnotationLayer = __webpack_exports__$1.AnnotationLayer;
var __webpack_exports__AnnotationMode = __webpack_exports__$1.AnnotationMode;
var __webpack_exports__ColorPicker = __webpack_exports__$1.ColorPicker;
var __webpack_exports__DOMSVGFactory = __webpack_exports__$1.DOMSVGFactory;
var __webpack_exports__DrawLayer = __webpack_exports__$1.DrawLayer;
var __webpack_exports__FeatureTest = __webpack_exports__$1.FeatureTest;
var __webpack_exports__GlobalWorkerOptions = __webpack_exports__$1.GlobalWorkerOptions;
var __webpack_exports__ImageKind = __webpack_exports__$1.ImageKind;
var __webpack_exports__InvalidPDFException = __webpack_exports__$1.InvalidPDFException;
var __webpack_exports__MissingPDFException = __webpack_exports__$1.MissingPDFException;
var __webpack_exports__OPS = __webpack_exports__$1.OPS;
var __webpack_exports__OutputScale = __webpack_exports__$1.OutputScale;
var __webpack_exports__PDFDataRangeTransport = __webpack_exports__$1.PDFDataRangeTransport;
var __webpack_exports__PDFDateString = __webpack_exports__$1.PDFDateString;
var __webpack_exports__PDFWorker = __webpack_exports__$1.PDFWorker;
var __webpack_exports__PasswordResponses = __webpack_exports__$1.PasswordResponses;
var __webpack_exports__PermissionFlag = __webpack_exports__$1.PermissionFlag;
var __webpack_exports__PixelsPerInch = __webpack_exports__$1.PixelsPerInch;
var __webpack_exports__RenderingCancelledException = __webpack_exports__$1.RenderingCancelledException;
var __webpack_exports__TextLayer = __webpack_exports__$1.TextLayer;
var __webpack_exports__TouchManager = __webpack_exports__$1.TouchManager;
var __webpack_exports__UnexpectedResponseException = __webpack_exports__$1.UnexpectedResponseException;
var __webpack_exports__Util = __webpack_exports__$1.Util;
var __webpack_exports__VerbosityLevel = __webpack_exports__$1.VerbosityLevel;
var __webpack_exports__XfaLayer = __webpack_exports__$1.XfaLayer;
var __webpack_exports__build = __webpack_exports__$1.build;
var __webpack_exports__createValidAbsoluteUrl = __webpack_exports__$1.createValidAbsoluteUrl;
var __webpack_exports__fetchData = __webpack_exports__$1.fetchData;
var __webpack_exports__getDocument = __webpack_exports__$1.getDocument;
var __webpack_exports__getFilenameFromUrl = __webpack_exports__$1.getFilenameFromUrl;
var __webpack_exports__getPdfFilenameFromUrl = __webpack_exports__$1.getPdfFilenameFromUrl;
var __webpack_exports__getXfaPageViewport = __webpack_exports__$1.getXfaPageViewport;
var __webpack_exports__isDataScheme = __webpack_exports__$1.isDataScheme;
var __webpack_exports__isPdfFile = __webpack_exports__$1.isPdfFile;
var __webpack_exports__noContextMenu = __webpack_exports__$1.noContextMenu;
var __webpack_exports__normalizeUnicode = __webpack_exports__$1.normalizeUnicode;
var __webpack_exports__setLayerDimensions = __webpack_exports__$1.setLayerDimensions;
var __webpack_exports__shadow = __webpack_exports__$1.shadow;
var __webpack_exports__stopEvent = __webpack_exports__$1.stopEvent;
var __webpack_exports__version = __webpack_exports__$1.version;
var pdf_viewer_export_exports = /* @__PURE__ */ __exportAll({
	AnnotationLayerBuilder: () => __webpack_exports__AnnotationLayerBuilder,
	DownloadManager: () => __webpack_exports__DownloadManager,
	EventBus: () => __webpack_exports__EventBus,
	FindState: () => __webpack_exports__FindState,
	GenericL10n: () => __webpack_exports__GenericL10n,
	LinkTarget: () => __webpack_exports__LinkTarget,
	PDFFindController: () => __webpack_exports__PDFFindController,
	PDFHistory: () => __webpack_exports__PDFHistory,
	PDFLinkService: () => __webpack_exports__PDFLinkService,
	PDFPageView: () => __webpack_exports__PDFPageView,
	PDFRenderingQueue: () => PDFRenderingQueue$1,
	PDFScriptingManager: () => __webpack_exports__PDFScriptingManager,
	PDFSinglePageViewer: () => __webpack_exports__PDFSinglePageViewer,
	PDFViewer: () => __webpack_exports__PDFViewer,
	ProgressBar: () => __webpack_exports__ProgressBar,
	RenderingStates: () => __webpack_exports__RenderingStates,
	ScrollMode: () => __webpack_exports__ScrollMode,
	SimpleLinkService: () => __webpack_exports__SimpleLinkService,
	SpreadMode: () => __webpack_exports__SpreadMode,
	StructTreeLayerBuilder: () => __webpack_exports__StructTreeLayerBuilder,
	TextLayerBuilder: () => __webpack_exports__TextLayerBuilder,
	XfaLayerBuilder: () => __webpack_exports__XfaLayerBuilder,
	parseQueryString: () => __webpack_exports__parseQueryString
});
function scrollIntoView(element, spot, scrollMatches = false) {
	let parent = element.offsetParent;
	if (!parent) {
		console.error("offsetParent is not set -- cannot scroll");
		return;
	}
	let offsetY = element.offsetTop + element.clientTop;
	let offsetX = element.offsetLeft + element.clientLeft;
	while (parent.clientHeight === parent.scrollHeight && parent.clientWidth === parent.scrollWidth || scrollMatches && (parent.classList.contains("markedContent") || getComputedStyle(parent).overflow === "hidden")) {
		offsetY += parent.offsetTop;
		offsetX += parent.offsetLeft;
		parent = parent.offsetParent;
		if (!parent) return;
	}
	if (spot) {
		if (spot.top !== void 0) offsetY += spot.top;
		if (spot.left !== void 0) {
			offsetX += spot.left;
			parent.scrollLeft = offsetX;
		}
	}
	parent.scrollTop = offsetY;
}
function watchScroll(viewAreaElement, callback, abortSignal = void 0) {
	const debounceScroll = function(evt) {
		if (rAF) return;
		rAF = window.requestAnimationFrame(function viewAreaElementScrolled() {
			rAF = null;
			const currentX = viewAreaElement.scrollLeft;
			const lastX = state.lastX;
			if (currentX !== lastX) state.right = currentX > lastX;
			state.lastX = currentX;
			const currentY = viewAreaElement.scrollTop;
			const lastY = state.lastY;
			if (currentY !== lastY) state.down = currentY > lastY;
			state.lastY = currentY;
			callback(state);
		});
	};
	const state = {
		right: true,
		down: true,
		lastX: viewAreaElement.scrollLeft,
		lastY: viewAreaElement.scrollTop,
		_eventHandler: debounceScroll
	};
	let rAF = null;
	viewAreaElement.addEventListener("scroll", debounceScroll, {
		useCapture: true,
		signal: abortSignal
	});
	abortSignal?.addEventListener("abort", () => window.cancelAnimationFrame(rAF), { once: true });
	return state;
}
function parseQueryString(query) {
	const params = /* @__PURE__ */ new Map();
	for (const [key, value] of new URLSearchParams(query)) params.set(key.toLowerCase(), value);
	return params;
}
function removeNullCharacters(str, replaceInvisible = false) {
	if (!InvisibleCharsRegExp.test(str)) return str;
	if (replaceInvisible) return str.replaceAll(InvisibleCharsRegExp, (m) => m === "\0" ? "" : " ");
	return str.replaceAll("\0", "");
}
function binarySearchFirstItem(items, condition, start = 0) {
	let minIndex = start;
	let maxIndex = items.length - 1;
	if (maxIndex < 0 || !condition(items[maxIndex])) return items.length;
	if (condition(items[minIndex])) return minIndex;
	while (minIndex < maxIndex) {
		const currentIndex = minIndex + maxIndex >> 1;
		const currentItem = items[currentIndex];
		if (condition(currentItem)) maxIndex = currentIndex;
		else minIndex = currentIndex + 1;
	}
	return minIndex;
}
function approximateFraction(x) {
	if (Math.floor(x) === x) return [x, 1];
	const xinv = 1 / x;
	const limit = 8;
	if (xinv > limit) return [1, limit];
	else if (Math.floor(xinv) === xinv) return [1, xinv];
	const x_ = x > 1 ? xinv : x;
	let a = 0, b = 1, c = 1, d = 1;
	while (true) {
		const p = a + c, q = b + d;
		if (q > limit) break;
		if (x_ <= p / q) {
			c = p;
			d = q;
		} else {
			a = p;
			b = q;
		}
	}
	let result;
	if (x_ - a / b < c / d - x_) result = x_ === x ? [a, b] : [b, a];
	else result = x_ === x ? [c, d] : [d, c];
	return result;
}
function floorToDivide(x, div) {
	return x - x % div;
}
function backtrackBeforeAllVisibleElements(index, views, top) {
	if (index < 2) return index;
	let elt = views[index].div;
	let pageTop = elt.offsetTop + elt.clientTop;
	if (pageTop >= top) {
		elt = views[index - 1].div;
		pageTop = elt.offsetTop + elt.clientTop;
	}
	for (let i = index - 2; i >= 0; --i) {
		elt = views[i].div;
		if (elt.offsetTop + elt.clientTop + elt.clientHeight <= pageTop) break;
		index = i;
	}
	return index;
}
function getVisibleElements({ scrollEl, views, sortByVisibility = false, horizontal = false, rtl = false }) {
	const top = scrollEl.scrollTop, bottom = top + scrollEl.clientHeight;
	const left = scrollEl.scrollLeft, right = left + scrollEl.clientWidth;
	function isElementBottomAfterViewTop(view) {
		const element = view.div;
		return element.offsetTop + element.clientTop + element.clientHeight > top;
	}
	function isElementNextAfterViewHorizontally(view) {
		const element = view.div;
		const elementLeft = element.offsetLeft + element.clientLeft;
		const elementRight = elementLeft + element.clientWidth;
		return rtl ? elementLeft < right : elementRight > left;
	}
	const visible = [], ids = /* @__PURE__ */ new Set(), numViews = views.length;
	let firstVisibleElementInd = binarySearchFirstItem(views, horizontal ? isElementNextAfterViewHorizontally : isElementBottomAfterViewTop);
	if (firstVisibleElementInd > 0 && firstVisibleElementInd < numViews && !horizontal) firstVisibleElementInd = backtrackBeforeAllVisibleElements(firstVisibleElementInd, views, top);
	let lastEdge = horizontal ? right : -1;
	for (let i = firstVisibleElementInd; i < numViews; i++) {
		const view = views[i], element = view.div;
		const currentWidth = element.offsetLeft + element.clientLeft;
		const currentHeight = element.offsetTop + element.clientTop;
		const viewWidth = element.clientWidth, viewHeight = element.clientHeight;
		const viewRight = currentWidth + viewWidth;
		const viewBottom = currentHeight + viewHeight;
		if (lastEdge === -1) {
			if (viewBottom >= bottom) lastEdge = viewBottom;
		} else if ((horizontal ? currentWidth : currentHeight) > lastEdge) break;
		if (viewBottom <= top || currentHeight >= bottom || viewRight <= left || currentWidth >= right) continue;
		const hiddenHeight = Math.max(0, top - currentHeight) + Math.max(0, viewBottom - bottom);
		const hiddenWidth = Math.max(0, left - currentWidth) + Math.max(0, viewRight - right);
		const fractionHeight = (viewHeight - hiddenHeight) / viewHeight, fractionWidth = (viewWidth - hiddenWidth) / viewWidth;
		const percent = fractionHeight * fractionWidth * 100 | 0;
		visible.push({
			id: view.id,
			x: currentWidth,
			y: currentHeight,
			view,
			percent,
			widthPercent: fractionWidth * 100 | 0
		});
		ids.add(view.id);
	}
	const first = visible[0], last = visible.at(-1);
	if (sortByVisibility) visible.sort(function(a, b) {
		const pc = a.percent - b.percent;
		if (Math.abs(pc) > .001) return -pc;
		return a.id - b.id;
	});
	return {
		first,
		last,
		views: visible,
		ids
	};
}
function isValidRotation(angle) {
	return Number.isInteger(angle) && angle % 90 === 0;
}
function isValidScrollMode(mode) {
	return Number.isInteger(mode) && Object.values(ScrollMode).includes(mode) && mode !== ScrollMode.UNKNOWN;
}
function isValidSpreadMode(mode) {
	return Number.isInteger(mode) && Object.values(SpreadMode).includes(mode) && mode !== SpreadMode.UNKNOWN;
}
function isPortraitOrientation(size) {
	return size.width <= size.height;
}
function clamp(v, min, max) {
	return Math.min(Math.max(v, min), max);
}
function apiPageLayoutToViewerModes(layout) {
	let scrollMode = ScrollMode.VERTICAL, spreadMode = SpreadMode.NONE;
	switch (layout) {
		case "SinglePage":
			scrollMode = ScrollMode.PAGE;
			break;
		case "OneColumn": break;
		case "TwoPageLeft": scrollMode = ScrollMode.PAGE;
		case "TwoColumnLeft":
			spreadMode = SpreadMode.ODD;
			break;
		case "TwoPageRight": scrollMode = ScrollMode.PAGE;
		case "TwoColumnRight": spreadMode = SpreadMode.EVEN;
	}
	return {
		scrollMode,
		spreadMode
	};
}
function isAlphabeticalScript(charCode) {
	return charCode < 11904;
}
function isAscii(charCode) {
	return (charCode & 65408) === 0;
}
function isAsciiAlpha(charCode) {
	return charCode >= 97 && charCode <= 122 || charCode >= 65 && charCode <= 90;
}
function isAsciiDigit(charCode) {
	return charCode >= 48 && charCode <= 57;
}
function isAsciiSpace(charCode) {
	return charCode === 32 || charCode === 9 || charCode === 13 || charCode === 10;
}
function isHan(charCode) {
	return charCode >= 13312 && charCode <= 40959 || charCode >= 63744 && charCode <= 64255;
}
function isKatakana(charCode) {
	return charCode >= 12448 && charCode <= 12543;
}
function isHiragana(charCode) {
	return charCode >= 12352 && charCode <= 12447;
}
function isHalfwidthKatakana(charCode) {
	return charCode >= 65376 && charCode <= 65439;
}
function isThai(charCode) {
	return (charCode & 65408) === 3584;
}
function getCharacterType(charCode) {
	if (isAlphabeticalScript(charCode)) {
		if (isAscii(charCode)) {
			if (isAsciiSpace(charCode)) return CharacterType.SPACE;
			else if (isAsciiAlpha(charCode) || isAsciiDigit(charCode) || charCode === 95) return CharacterType.ALPHA_LETTER;
			return CharacterType.PUNCT;
		} else if (isThai(charCode)) return CharacterType.THAI_LETTER;
		else if (charCode === 160) return CharacterType.SPACE;
		return CharacterType.ALPHA_LETTER;
	}
	if (isHan(charCode)) return CharacterType.HAN_LETTER;
	else if (isKatakana(charCode)) return CharacterType.KATAKANA_LETTER;
	else if (isHiragana(charCode)) return CharacterType.HIRAGANA_LETTER;
	else if (isHalfwidthKatakana(charCode)) return CharacterType.HALFWIDTH_KATAKANA_LETTER;
	return CharacterType.ALPHA_LETTER;
}
function getNormalizeWithNFKC() {
	NormalizeWithNFKC ||= ` ¨ª¯²-µ¸-º¼-¾Ĳ-ĳĿ-ŀŉſǄ-ǌǱ-ǳʰ-ʸ˘-˝ˠ-ˤʹͺ;΄-΅·ϐ-ϖϰ-ϲϴ-ϵϹևٵ-ٸक़-य़ড়-ঢ়য়ਲ਼ਸ਼ਖ਼-ਜ਼ਫ਼ଡ଼-ଢ଼ำຳໜ-ໝ༌གྷཌྷདྷབྷཛྷཀྵჼᴬ-ᴮᴰ-ᴺᴼ-ᵍᵏ-ᵪᵸᶛ-ᶿẚ-ẛάέήίόύώΆ᾽-῁ΈΉ῍-῏ΐΊ῝-῟ΰΎ῭-`ΌΏ´-῾ - ‑‗․-… ″-‴‶-‷‼‾⁇-⁉⁗ ⁰-ⁱ⁴-₎ₐ-ₜ₨℀-℃℅-ℇ℉-ℓℕ-№ℙ-ℝ℠-™ℤΩℨK-ℭℯ-ℱℳ-ℹ℻-⅀ⅅ-ⅉ⅐-ⅿ↉∬-∭∯-∰〈-〉①-⓪⨌⩴-⩶⫝̸ⱼ-ⱽⵯ⺟⻳⼀-⿕　〶〸-〺゛-゜ゟヿㄱ-ㆎ㆒-㆟㈀-㈞㈠-㉇㉐-㉾㊀-㏿ꚜ-ꚝꝰꟲ-ꟴꟸ-ꟹꭜ-ꭟꭩ豈-嗀塚晴凞-羽蘒諸逸-都飯-舘並-龎ﬀ-ﬆﬓ-ﬗיִײַ-זּטּ-לּמּנּ-סּףּ-פּצּ-ﮱﯓ-ﴽﵐ-ﶏﶒ-ﷇﷰ-﷼︐-︙︰-﹄﹇-﹒﹔-﹦﹨-﹫ﹰ-ﹲﹴﹶ-ﻼ！-ﾾￂ-ￇￊ-ￏￒ-ￗￚ-ￜ￠-￦`;
	return NormalizeWithNFKC;
}
function normalize(text) {
	const syllablePositions = [];
	let m;
	while ((m = SYLLABLES_REG_EXP.exec(text)) !== null) {
		let { index } = m;
		for (const char of m[0]) {
			let len = SYLLABLES_LENGTHS.get(char);
			if (!len) {
				len = char.normalize("NFD").length;
				SYLLABLES_LENGTHS.set(char, len);
			}
			syllablePositions.push([len, index++]);
		}
	}
	let normalizationRegex;
	if (syllablePositions.length === 0 && noSyllablesRegExp) normalizationRegex = noSyllablesRegExp;
	else if (syllablePositions.length > 0 && withSyllablesRegExp) normalizationRegex = withSyllablesRegExp;
	else {
		const regexp = `([${Object.keys(CHARACTERS_TO_NORMALIZE).join("")}])|([${getNormalizeWithNFKC()}])|((?:゙|゚)\\n)|(\\p{M}+(?:-\\n)?)|(\\p{Ll}-\\n\\p{Lu})|(\\S-\\n)|((?:\\p{Ideographic}|[぀-ヿ])\\n)|(\\n)`;
		if (syllablePositions.length === 0) normalizationRegex = noSyllablesRegExp = new RegExp(regexp + "|(\\u0000)", "gum");
		else normalizationRegex = withSyllablesRegExp = new RegExp(regexp + `|(${FIRST_CHAR_SYLLABLES_REG_EXP})`, "gum");
	}
	const rawDiacriticsPositions = [];
	while ((m = DIACRITICS_REG_EXP.exec(text)) !== null) rawDiacriticsPositions.push([m[0].length, m.index]);
	let normalized = text.normalize("NFD");
	const positions = [0, 0];
	let rawDiacriticsIndex = 0;
	let syllableIndex = 0;
	let shift = 0;
	let shiftOrigin = 0;
	let eol = 0;
	let hasDiacritics = false;
	normalized = normalized.replace(normalizationRegex, (match, p1, p2, p3, p4, p5, p6, p7, p8, p9, i) => {
		i -= shiftOrigin;
		if (p1) {
			const replacement = CHARACTERS_TO_NORMALIZE[p1];
			const jj = replacement.length;
			for (let j = 1; j < jj; j++) positions.push(i - shift + j, shift - j);
			shift -= jj - 1;
			return replacement;
		}
		if (p2) {
			let replacement = NFKC_CHARS_TO_NORMALIZE.get(p2);
			if (!replacement) {
				replacement = p2.normalize("NFKC");
				NFKC_CHARS_TO_NORMALIZE.set(p2, replacement);
			}
			const jj = replacement.length;
			for (let j = 1; j < jj; j++) positions.push(i - shift + j, shift - j);
			shift -= jj - 1;
			return replacement;
		}
		if (p3) {
			hasDiacritics = true;
			if (i + eol === rawDiacriticsPositions[rawDiacriticsIndex]?.[1]) ++rawDiacriticsIndex;
			else {
				positions.push(i - 1 - shift + 1, shift - 1);
				shift -= 1;
				shiftOrigin += 1;
			}
			positions.push(i - shift + 1, shift);
			shiftOrigin += 1;
			eol += 1;
			return p3.charAt(0);
		}
		if (p4) {
			const hasTrailingDashEOL = p4.endsWith("\n");
			const len = hasTrailingDashEOL ? p4.length - 2 : p4.length;
			hasDiacritics = true;
			let jj = len;
			if (i + eol === rawDiacriticsPositions[rawDiacriticsIndex]?.[1]) {
				jj -= rawDiacriticsPositions[rawDiacriticsIndex][0];
				++rawDiacriticsIndex;
			}
			for (let j = 1; j <= jj; j++) positions.push(i - 1 - shift + j, shift - j);
			shift -= jj;
			shiftOrigin += jj;
			if (hasTrailingDashEOL) {
				i += len - 1;
				positions.push(i - shift + 1, 1 + shift);
				shift += 1;
				shiftOrigin += 1;
				eol += 1;
				return p4.slice(0, len);
			}
			return p4;
		}
		if (p5) {
			shiftOrigin += 1;
			eol += 1;
			return p5.replace("\n", "");
		}
		if (p6) {
			const len = p6.length - 2;
			positions.push(i - shift + len, 1 + shift);
			shift += 1;
			shiftOrigin += 1;
			eol += 1;
			return p6.slice(0, -2);
		}
		if (p7) {
			const len = p7.length - 1;
			positions.push(i - shift + len, shift);
			shiftOrigin += 1;
			eol += 1;
			return p7.slice(0, -1);
		}
		if (p8) {
			positions.push(i - shift + 1, shift - 1);
			shift -= 1;
			shiftOrigin += 1;
			eol += 1;
			return " ";
		}
		if (i + eol === syllablePositions[syllableIndex]?.[1]) {
			const newCharLen = syllablePositions[syllableIndex][0] - 1;
			++syllableIndex;
			for (let j = 1; j <= newCharLen; j++) positions.push(i - (shift - j), shift - j);
			shift -= newCharLen;
			shiftOrigin += newCharLen;
		}
		return p9;
	});
	positions.push(normalized.length, shift);
	const starts = new Uint32Array(positions.length >> 1);
	const shifts = new Int32Array(positions.length >> 1);
	for (let i = 0, ii = positions.length; i < ii; i += 2) {
		starts[i >> 1] = positions[i];
		shifts[i >> 1] = positions[i + 1];
	}
	return [
		normalized,
		[starts, shifts],
		hasDiacritics
	];
}
function getOriginalIndex(diffs, pos, len) {
	if (!diffs) return [pos, len];
	const [starts, shifts] = diffs;
	const start = pos;
	const end = pos + len - 1;
	let i = binarySearchFirstItem(starts, (x) => x >= start);
	if (starts[i] > start) --i;
	let j = binarySearchFirstItem(starts, (x) => x >= end, i);
	if (starts[j] > end) --j;
	const oldStart = start + shifts[i];
	return [oldStart, end + shifts[j] + 1 - oldStart];
}
function download(blobUrl, filename) {
	const a = document.createElement("a");
	if (!a.click) throw new Error("DownloadManager: \"a.click()\" is not supported.");
	a.href = blobUrl;
	a.target = "_parent";
	if ("download" in a) a.download = filename;
	(document.body || document.documentElement).append(a);
	a.click();
	a.remove();
}
async function waitOnEventOrTimeout({ target, name, delay = 0 }) {
	if (typeof target !== "object" || !(name && typeof name === "string") || !(Number.isInteger(delay) && delay >= 0)) throw new Error("waitOnEventOrTimeout - invalid parameters.");
	const { promise, resolve } = Promise.withResolvers();
	const ac = new AbortController();
	function handler(type) {
		ac.abort();
		clearTimeout(timeout);
		resolve(type);
	}
	target[target instanceof EventBus$1 ? "_on" : "addEventListener"](name, handler.bind(null, WaitOnType.EVENT), { signal: ac.signal });
	const timeout = setTimeout(handler.bind(null, WaitOnType.TIMEOUT), delay);
	return promise;
}
function match(scope, selector, key) {
	if (key === selector) return true;
	if (key instanceof FluentNumber && selector instanceof FluentNumber && key.value === selector.value) return true;
	if (selector instanceof FluentNumber && typeof key === "string") {
		if (key === scope.memoizeIntlObject(Intl.PluralRules, selector.opts).select(selector.value)) return true;
	}
	return false;
}
function getDefault(scope, variants, star) {
	if (variants[star]) return resolvePattern(scope, variants[star].value);
	scope.reportError(/* @__PURE__ */ new RangeError("No default"));
	return new FluentNone();
}
function getArguments(scope, args) {
	const positional = [];
	const named = Object.create(null);
	for (const arg of args) if (arg.type === "narg") named[arg.name] = resolveExpression(scope, arg.value);
	else positional.push(resolveExpression(scope, arg));
	return {
		positional,
		named
	};
}
function resolveExpression(scope, expr) {
	switch (expr.type) {
		case "str": return expr.value;
		case "num": return new FluentNumber(expr.value, { minimumFractionDigits: expr.precision });
		case "var": return resolveVariableReference(scope, expr);
		case "mesg": return resolveMessageReference(scope, expr);
		case "term": return resolveTermReference(scope, expr);
		case "func": return resolveFunctionReference(scope, expr);
		case "select": return resolveSelectExpression(scope, expr);
		default: return new FluentNone();
	}
}
function resolveVariableReference(scope, { name }) {
	let arg;
	if (scope.params) {
		if (Object.prototype.hasOwnProperty.call(scope.params, name)) arg = scope.params[name];
		else return new FluentNone(`$${name}`);
	} else if (scope.args && Object.prototype.hasOwnProperty.call(scope.args, name)) arg = scope.args[name];
	else {
		scope.reportError(/* @__PURE__ */ new ReferenceError(`Unknown variable: $${name}`));
		return new FluentNone(`$${name}`);
	}
	if (arg instanceof FluentType) return arg;
	switch (typeof arg) {
		case "string": return arg;
		case "number": return new FluentNumber(arg);
		case "object": if (arg instanceof Date) return new FluentDateTime(arg.getTime());
		default:
			scope.reportError(/* @__PURE__ */ new TypeError(`Variable type not supported: $${name}, ${typeof arg}`));
			return new FluentNone(`$${name}`);
	}
}
function resolveMessageReference(scope, { name, attr }) {
	const message = scope.bundle._messages.get(name);
	if (!message) {
		scope.reportError(/* @__PURE__ */ new ReferenceError(`Unknown message: ${name}`));
		return new FluentNone(name);
	}
	if (attr) {
		const attribute = message.attributes[attr];
		if (attribute) return resolvePattern(scope, attribute);
		scope.reportError(/* @__PURE__ */ new ReferenceError(`Unknown attribute: ${attr}`));
		return new FluentNone(`${name}.${attr}`);
	}
	if (message.value) return resolvePattern(scope, message.value);
	scope.reportError(/* @__PURE__ */ new ReferenceError(`No value: ${name}`));
	return new FluentNone(name);
}
function resolveTermReference(scope, { name, attr, args }) {
	const id = `-${name}`;
	const term = scope.bundle._terms.get(id);
	if (!term) {
		scope.reportError(/* @__PURE__ */ new ReferenceError(`Unknown term: ${id}`));
		return new FluentNone(id);
	}
	if (attr) {
		const attribute = term.attributes[attr];
		if (attribute) {
			scope.params = getArguments(scope, args).named;
			const resolved = resolvePattern(scope, attribute);
			scope.params = null;
			return resolved;
		}
		scope.reportError(/* @__PURE__ */ new ReferenceError(`Unknown attribute: ${attr}`));
		return new FluentNone(`${id}.${attr}`);
	}
	scope.params = getArguments(scope, args).named;
	const resolved = resolvePattern(scope, term.value);
	scope.params = null;
	return resolved;
}
function resolveFunctionReference(scope, { name, args }) {
	let func = scope.bundle._functions[name];
	if (!func) {
		scope.reportError(/* @__PURE__ */ new ReferenceError(`Unknown function: ${name}()`));
		return new FluentNone(`${name}()`);
	}
	if (typeof func !== "function") {
		scope.reportError(/* @__PURE__ */ new TypeError(`Function ${name}() is not callable`));
		return new FluentNone(`${name}()`);
	}
	try {
		let resolved = getArguments(scope, args);
		return func(resolved.positional, resolved.named);
	} catch (err) {
		scope.reportError(err);
		return new FluentNone(`${name}()`);
	}
}
function resolveSelectExpression(scope, { selector, variants, star }) {
	let sel = resolveExpression(scope, selector);
	if (sel instanceof FluentNone) return getDefault(scope, variants, star);
	for (const variant of variants) if (match(scope, sel, resolveExpression(scope, variant.key))) return resolvePattern(scope, variant.value);
	return getDefault(scope, variants, star);
}
function resolveComplexPattern(scope, ptn) {
	if (scope.dirty.has(ptn)) {
		scope.reportError(/* @__PURE__ */ new RangeError("Cyclic reference"));
		return new FluentNone();
	}
	scope.dirty.add(ptn);
	const result = [];
	const useIsolating = scope.bundle._useIsolating && ptn.length > 1;
	for (const elem of ptn) {
		if (typeof elem === "string") {
			result.push(scope.bundle._transform(elem));
			continue;
		}
		scope.placeables++;
		if (scope.placeables > MAX_PLACEABLES) {
			scope.dirty.delete(ptn);
			throw new RangeError(`Too many placeables expanded: ${scope.placeables}, max allowed is ${MAX_PLACEABLES}`);
		}
		if (useIsolating) result.push(FSI);
		result.push(resolveExpression(scope, elem).toString(scope));
		if (useIsolating) result.push(PDI);
	}
	scope.dirty.delete(ptn);
	return result.join("");
}
function resolvePattern(scope, value) {
	if (typeof value === "string") return scope.bundle._transform(value);
	return resolveComplexPattern(scope, value);
}
function values(opts, allowed) {
	const unwrapped = Object.create(null);
	for (const [name, opt] of Object.entries(opts)) if (allowed.includes(name)) unwrapped[name] = opt.valueOf();
	return unwrapped;
}
function NUMBER(args, opts) {
	let arg = args[0];
	if (arg instanceof FluentNone) return new FluentNone(`NUMBER(${arg.valueOf()})`);
	if (arg instanceof FluentNumber) return new FluentNumber(arg.valueOf(), {
		...arg.opts,
		...values(opts, NUMBER_ALLOWED)
	});
	if (arg instanceof FluentDateTime) return new FluentNumber(arg.valueOf(), { ...values(opts, NUMBER_ALLOWED) });
	throw new TypeError("Invalid argument to NUMBER");
}
function DATETIME(args, opts) {
	let arg = args[0];
	if (arg instanceof FluentNone) return new FluentNone(`DATETIME(${arg.valueOf()})`);
	if (arg instanceof FluentDateTime) return new FluentDateTime(arg.valueOf(), {
		...arg.opts,
		...values(opts, DATETIME_ALLOWED)
	});
	if (arg instanceof FluentNumber) return new FluentDateTime(arg.valueOf(), { ...values(opts, DATETIME_ALLOWED) });
	throw new TypeError("Invalid argument to DATETIME");
}
function getMemoizerForLocale(locales) {
	const stringLocale = Array.isArray(locales) ? locales.join(" ") : locales;
	let memoizer = cache.get(stringLocale);
	if (memoizer === void 0) {
		memoizer = /* @__PURE__ */ new Map();
		cache.set(stringLocale, memoizer);
	}
	return memoizer;
}
function translateElement(element, translation) {
	const { value } = translation;
	if (typeof value === "string") {
		if (element.localName === "title" && element.namespaceURI === "http://www.w3.org/1999/xhtml") element.textContent = value;
		else if (!reOverlay.test(value)) element.textContent = value;
		else {
			const templateElement = element.ownerDocument.createElementNS("http://www.w3.org/1999/xhtml", "template");
			templateElement.innerHTML = value;
			overlayChildNodes(templateElement.content, element);
		}
	}
	overlayAttributes(translation, element);
}
function overlayChildNodes(fromFragment, toElement) {
	for (const childNode of fromFragment.childNodes) {
		if (childNode.nodeType === childNode.TEXT_NODE) continue;
		if (childNode.hasAttribute("data-l10n-name")) {
			const sanitized = getNodeForNamedElement(toElement, childNode);
			fromFragment.replaceChild(sanitized, childNode);
			continue;
		}
		if (isElementAllowed(childNode)) {
			const sanitized = createSanitizedElement(childNode);
			fromFragment.replaceChild(sanitized, childNode);
			continue;
		}
		console.warn(`An element of forbidden type "${childNode.localName}" was found in the translation. Only safe text-level elements and elements with data-l10n-name are allowed.`);
		fromFragment.replaceChild(createTextNodeFromTextContent(childNode), childNode);
	}
	toElement.textContent = "";
	toElement.appendChild(fromFragment);
}
function hasAttribute(attributes, name) {
	if (!attributes) return false;
	for (let attr of attributes) if (attr.name === name) return true;
	return false;
}
function overlayAttributes(fromElement, toElement) {
	const explicitlyAllowed = toElement.hasAttribute("data-l10n-attrs") ? toElement.getAttribute("data-l10n-attrs").split(",").map((i) => i.trim()) : null;
	for (const attr of Array.from(toElement.attributes)) if (isAttrNameLocalizable(attr.name, toElement, explicitlyAllowed) && !hasAttribute(fromElement.attributes, attr.name)) toElement.removeAttribute(attr.name);
	if (!fromElement.attributes) return;
	for (const attr of Array.from(fromElement.attributes)) if (isAttrNameLocalizable(attr.name, toElement, explicitlyAllowed) && toElement.getAttribute(attr.name) !== attr.value) toElement.setAttribute(attr.name, attr.value);
}
function getNodeForNamedElement(sourceElement, translatedChild) {
	const childName = translatedChild.getAttribute("data-l10n-name");
	const sourceChild = sourceElement.querySelector(`[data-l10n-name="${childName}"]`);
	if (!sourceChild) {
		console.warn(`An element named "${childName}" wasn't found in the source.`);
		return createTextNodeFromTextContent(translatedChild);
	}
	if (sourceChild.localName !== translatedChild.localName) {
		console.warn(`An element named "${childName}" was found in the translation but its type ${translatedChild.localName} didn't match the element found in the source (${sourceChild.localName}).`);
		return createTextNodeFromTextContent(translatedChild);
	}
	sourceElement.removeChild(sourceChild);
	return shallowPopulateUsing(translatedChild, sourceChild.cloneNode(false));
}
function createSanitizedElement(element) {
	return shallowPopulateUsing(element, element.ownerDocument.createElement(element.localName));
}
function createTextNodeFromTextContent(element) {
	return element.ownerDocument.createTextNode(element.textContent);
}
function isElementAllowed(element) {
	const allowed = TEXT_LEVEL_ELEMENTS[element.namespaceURI];
	return allowed && allowed.includes(element.localName);
}
function isAttrNameLocalizable(name, element, explicitlyAllowed = null) {
	if (explicitlyAllowed && explicitlyAllowed.includes(name)) return true;
	const allowed = LOCALIZABLE_ATTRIBUTES[element.namespaceURI];
	if (!allowed) return false;
	const attrName = name.toLowerCase();
	const elemName = element.localName;
	if (allowed.global.includes(attrName)) return true;
	if (!allowed[elemName]) return false;
	if (allowed[elemName].includes(attrName)) return true;
	if (element.namespaceURI === "http://www.w3.org/1999/xhtml" && elemName === "input" && attrName === "value") {
		const type = element.type.toLowerCase();
		if (type === "submit" || type === "button" || type === "reset") return true;
	}
	return false;
}
function shallowPopulateUsing(fromElement, toElement) {
	toElement.textContent = fromElement.textContent;
	overlayAttributes(fromElement, toElement);
	return toElement;
}
function valueFromBundle(bundle, errors, message, args) {
	if (message.value) return bundle.formatPattern(message.value, args, errors);
	return null;
}
function messageFromBundle(bundle, errors, message, args) {
	const formatted = {
		value: null,
		attributes: null
	};
	if (message.value) formatted.value = bundle.formatPattern(message.value, args, errors);
	let attrNames = Object.keys(message.attributes);
	if (attrNames.length > 0) {
		formatted.attributes = new Array(attrNames.length);
		for (let [i, name] of attrNames.entries()) {
			let value = bundle.formatPattern(message.attributes[name], args, errors);
			formatted.attributes[i] = {
				name,
				value
			};
		}
	}
	return formatted;
}
function keysFromBundle(method, bundle, keys, translations) {
	const messageErrors = [];
	const missingIds = /* @__PURE__ */ new Set();
	keys.forEach(({ id, args }, i) => {
		if (translations[i] !== void 0) return;
		let message = bundle.getMessage(id);
		if (message) {
			messageErrors.length = 0;
			translations[i] = method(bundle, messageErrors, message, args);
			if (messageErrors.length > 0 && typeof console !== "undefined") {
				const locale = bundle.locales[0];
				const errors = messageErrors.join(", ");
				console.warn(`[fluent][resolver] errors in ${locale}/${id}: ${errors}.`);
			}
		} else missingIds.add(id);
	});
	return missingIds;
}
function createBundle(lang, text) {
	const resource = new FluentResource(text);
	const bundle = new FluentBundle(lang);
	const errors = bundle.addResource(resource);
	if (errors.length) console.error("L10n errors", errors);
	return bundle;
}
function getCurrentHash() {
	return document.location.hash;
}
function isDestHashesEqual(destHash, pushHash) {
	if (typeof destHash !== "string" || typeof pushHash !== "string") return false;
	if (destHash === pushHash) return true;
	if (parseQueryString(destHash).get("nameddest") === pushHash) return true;
	return false;
}
function isDestArraysEqual(firstDest, secondDest) {
	function isEntryEqual(first, second) {
		if (typeof first !== typeof second) return false;
		if (Array.isArray(first) || Array.isArray(second)) return false;
		if (first !== null && typeof first === "object" && second !== null) {
			if (Object.keys(first).length !== Object.keys(second).length) return false;
			for (const key in first) if (!isEntryEqual(first[key], second[key])) return false;
			return true;
		}
		return first === second || Number.isNaN(first) && Number.isNaN(second);
	}
	if (!(Array.isArray(firstDest) && Array.isArray(secondDest))) return false;
	if (firstDest.length !== secondDest.length) return false;
	for (let i = 0, ii = firstDest.length; i < ii; i++) if (!isEntryEqual(firstDest[i], secondDest[i])) return false;
	return true;
}
async function docProperties(pdfDocument) {
	const url = "", baseUrl = url.split("#", 1)[0];
	let { info, metadata, contentDispositionFilename, contentLength } = await pdfDocument.getMetadata();
	if (!contentLength) {
		const { length } = await pdfDocument.getDownloadInfo();
		contentLength = length;
	}
	return {
		...info,
		baseURL: baseUrl,
		filesize: contentLength,
		filename: contentDispositionFilename || getPdfFilenameFromUrl(url),
		metadata: metadata?.getRaw(),
		authors: metadata?.get("dc:creator"),
		numPages: pdfDocument.numPages,
		URL: url
	};
}
function isValidAnnotationEditorMode(mode) {
	return Object.values(AnnotationEditorType).includes(mode) && mode !== AnnotationEditorType.DISABLE;
}
var __webpack_require__;
var __webpack_exports__;
var DEFAULT_SCALE_VALUE;
var DEFAULT_SCALE;
var DEFAULT_SCALE_DELTA;
var MIN_SCALE;
var MAX_SCALE;
var UNKNOWN_SCALE;
var MAX_AUTO_SCALE;
var SCROLLBAR_PADDING;
var VERTICAL_PADDING;
var RenderingStates;
var PresentationModeState;
var TextLayerMode;
var ScrollMode;
var SpreadMode;
var InvisibleCharsRegExp;
var docStyle;
var ProgressBar;
var calcRound;
var CharacterType;
var NormalizeWithNFKC;
var FindState;
var FIND_TIMEOUT;
var MATCH_SCROLL_OFFSET_TOP;
var MATCH_SCROLL_OFFSET_LEFT;
var CHARACTERS_TO_NORMALIZE;
var DIACRITICS_EXCEPTION;
var DIACRITICS_EXCEPTION_STR;
var DIACRITICS_REG_EXP;
var SPECIAL_CHARS_REG_EXP;
var NOT_DIACRITIC_FROM_END_REG_EXP;
var NOT_DIACRITIC_FROM_START_REG_EXP;
var SYLLABLES_REG_EXP;
var SYLLABLES_LENGTHS;
var FIRST_CHAR_SYLLABLES_REG_EXP;
var NFKC_CHARS_TO_NORMALIZE;
var noSyllablesRegExp;
var withSyllablesRegExp;
var PDFFindController;
var DEFAULT_LINK_REL;
var LinkTarget;
var PDFLinkService$1;
var SimpleLinkService;
var AbortException;
var AnnotationEditorLayer;
var AnnotationEditorParamsType;
var AnnotationEditorType;
var AnnotationEditorUIManager;
var AnnotationLayer;
var AnnotationMode;
var build;
var ColorPicker;
var createValidAbsoluteUrl;
var DOMSVGFactory;
var DrawLayer;
var FeatureTest;
var fetchData;
var getDocument$1;
var getFilenameFromUrl;
var getPdfFilenameFromUrl;
var getXfaPageViewport;
var GlobalWorkerOptions$1;
var ImageKind;
var InvalidPDFException;
var isDataScheme;
var isPdfFile;
var MissingPDFException;
var noContextMenu;
var normalizeUnicode;
var OPS;
var OutputScale;
var PasswordResponses;
var PDFDataRangeTransport;
var PDFDateString;
var PDFWorker;
var PermissionFlag;
var PixelsPerInch;
var RenderingCancelledException;
var setLayerDimensions;
var shadow;
var stopEvent;
var TextLayer;
var TouchManager;
var UnexpectedResponseException;
var Util;
var VerbosityLevel;
var version$1;
var XfaLayer;
var AnnotationLayerBuilder;
var DownloadManager;
var WaitOnType;
var EventBus$1;
var FluentType;
var FluentNone;
var FluentNumber;
var FluentDateTime;
var MAX_PLACEABLES;
var FSI;
var PDI;
var Scope;
var NUMBER_ALLOWED;
var DATETIME_ALLOWED;
var cache;
var FluentBundle;
var RE_MESSAGE_START;
var RE_ATTRIBUTE_START;
var RE_VARIANT_START;
var RE_NUMBER_LITERAL;
var RE_IDENTIFIER;
var RE_REFERENCE;
var RE_FUNCTION_NAME;
var RE_TEXT_RUN;
var RE_STRING_RUN;
var RE_STRING_ESCAPE;
var RE_UNICODE_ESCAPE;
var RE_LEADING_NEWLINES;
var RE_TRAILING_SPACES;
var RE_BLANK_LINES;
var RE_INDENT;
var TOKEN_BRACE_OPEN;
var TOKEN_BRACE_CLOSE;
var TOKEN_BRACKET_OPEN;
var TOKEN_BRACKET_CLOSE;
var TOKEN_PAREN_OPEN;
var TOKEN_ARROW;
var TOKEN_COLON;
var TOKEN_COMMA;
var TOKEN_BLANK;
var FluentResource;
var Indent;
var reOverlay;
var TEXT_LEVEL_ELEMENTS;
var LOCALIZABLE_ATTRIBUTES;
var CachedIterable;
var CachedAsyncIterable;
var Localization;
var L10NID_ATTR_NAME;
var L10NARGS_ATTR_NAME;
var L10N_ELEMENT_QUERY;
var DOMLocalization;
var L10n;
var genericl10n_GenericL10n;
var HASH_CHANGE_TIMEOUT;
var POSITION_UPDATED_THRESHOLD;
var UPDATE_VIEWAREA_TIMEOUT;
var PDFHistory;
var AnnotationEditorLayerBuilder;
var compatParams;
var OptionKind;
var Type;
var defaultOptions;
var AppOptions;
var DrawLayerBuilder;
var PDF_ROLE_TO_HTML_ROLE;
var HEADING_PATTERN;
var StructTreeLayerBuilder;
var TextAccessibilityManager;
var TextHighlighter;
var TextLayerBuilder;
var XfaLayerBuilder;
var DEFAULT_LAYER_PROPERTIES;
var LAYERS_ORDER;
var PDFPageView;
var GenericScripting;
var PDFScriptingManager;
var PDFScriptingManagerComponents;
var CLEANUP_TIMEOUT;
var PDFRenderingQueue$1;
var DEFAULT_CACHE_SIZE;
var PagesCountLimit;
var PDFPageViewBuffer;
var PDFViewer$1;
var PDFSinglePageViewer;
var __webpack_exports__AnnotationLayerBuilder;
var __webpack_exports__DownloadManager;
var __webpack_exports__EventBus;
var __webpack_exports__FindState;
var __webpack_exports__GenericL10n;
var __webpack_exports__LinkTarget;
var __webpack_exports__PDFFindController;
var __webpack_exports__PDFHistory;
var __webpack_exports__PDFLinkService;
var __webpack_exports__PDFPageView;
var __webpack_exports__PDFScriptingManager;
var __webpack_exports__PDFSinglePageViewer;
var __webpack_exports__PDFViewer;
var __webpack_exports__ProgressBar;
var __webpack_exports__RenderingStates;
var __webpack_exports__ScrollMode;
var __webpack_exports__SimpleLinkService;
var __webpack_exports__SpreadMode;
var __webpack_exports__StructTreeLayerBuilder;
var __webpack_exports__TextLayerBuilder;
var __webpack_exports__XfaLayerBuilder;
var __webpack_exports__parseQueryString;
var init_pdf_viewer_export = __esmMin((() => {
	__webpack_require__ = {};
	(() => {
		__webpack_require__.d = (exports, definition) => {
			for (var key in definition) if (__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) Object.defineProperty(exports, key, {
				enumerable: true,
				get: definition[key]
			});
		};
	})();
	(() => {
		__webpack_require__.o = (obj, prop) => Object.prototype.hasOwnProperty.call(obj, prop);
	})();
	__webpack_exports__ = globalThis.pdfjsViewer = {};
	__webpack_require__.d(__webpack_exports__, {
		AnnotationLayerBuilder: () => AnnotationLayerBuilder,
		DownloadManager: () => DownloadManager,
		EventBus: () => EventBus$1,
		FindState: () => FindState,
		GenericL10n: () => genericl10n_GenericL10n,
		LinkTarget: () => LinkTarget,
		PDFFindController: () => PDFFindController,
		PDFHistory: () => PDFHistory,
		PDFLinkService: () => PDFLinkService$1,
		PDFPageView: () => PDFPageView,
		PDFScriptingManager: () => PDFScriptingManagerComponents,
		PDFSinglePageViewer: () => PDFSinglePageViewer,
		PDFViewer: () => PDFViewer$1,
		ProgressBar: () => ProgressBar,
		RenderingStates: () => RenderingStates,
		ScrollMode: () => ScrollMode,
		SimpleLinkService: () => SimpleLinkService,
		SpreadMode: () => SpreadMode,
		StructTreeLayerBuilder: () => StructTreeLayerBuilder,
		TextLayerBuilder: () => TextLayerBuilder,
		XfaLayerBuilder: () => XfaLayerBuilder,
		parseQueryString: () => parseQueryString
	});
	DEFAULT_SCALE_VALUE = "auto";
	DEFAULT_SCALE = 1;
	DEFAULT_SCALE_DELTA = 1.1;
	MIN_SCALE = .1;
	MAX_SCALE = 10;
	UNKNOWN_SCALE = 0;
	MAX_AUTO_SCALE = 1.25;
	SCROLLBAR_PADDING = 40;
	VERTICAL_PADDING = 5;
	RenderingStates = {
		INITIAL: 0,
		RUNNING: 1,
		PAUSED: 2,
		FINISHED: 3
	};
	PresentationModeState = {
		UNKNOWN: 0,
		NORMAL: 1,
		CHANGING: 2,
		FULLSCREEN: 3
	};
	TextLayerMode = {
		DISABLE: 0,
		ENABLE: 1,
		ENABLE_PERMISSIONS: 2
	};
	ScrollMode = {
		UNKNOWN: -1,
		VERTICAL: 0,
		HORIZONTAL: 1,
		WRAPPED: 2,
		PAGE: 3
	};
	SpreadMode = {
		UNKNOWN: -1,
		NONE: 0,
		ODD: 1,
		EVEN: 2
	};
	InvisibleCharsRegExp = /[\x00-\x1F]/g;
	new Promise(function(resolve) {
		window.requestAnimationFrame(resolve);
	});
	docStyle = document.documentElement.style;
	ProgressBar = class {
		#classList = null;
		#disableAutoFetchTimeout = null;
		#percent = 0;
		#style = null;
		#visible = true;
		constructor(bar) {
			this.#classList = bar.classList;
			this.#style = bar.style;
		}
		get percent() {
			return this.#percent;
		}
		set percent(val) {
			this.#percent = clamp(val, 0, 100);
			if (isNaN(val)) {
				this.#classList.add("indeterminate");
				return;
			}
			this.#classList.remove("indeterminate");
			this.#style.setProperty("--progressBar-percent", `${this.#percent}%`);
		}
		setWidth(viewer) {
			if (!viewer) return;
			const scrollbarWidth = viewer.parentNode.offsetWidth - viewer.offsetWidth;
			if (scrollbarWidth > 0) this.#style.setProperty("--progressBar-end-offset", `${scrollbarWidth}px`);
		}
		setDisableAutoFetch(delay = 5e3) {
			if (this.#percent === 100 || isNaN(this.#percent)) return;
			if (this.#disableAutoFetchTimeout) clearTimeout(this.#disableAutoFetchTimeout);
			this.show();
			this.#disableAutoFetchTimeout = setTimeout(() => {
				this.#disableAutoFetchTimeout = null;
				this.hide();
			}, delay);
		}
		hide() {
			if (!this.#visible) return;
			this.#visible = false;
			this.#classList.add("hidden");
		}
		show() {
			if (this.#visible) return;
			this.#visible = true;
			this.#classList.remove("hidden");
		}
	};
	calcRound = function() {
		const e = document.createElement("div");
		e.style.width = "round(down, calc(1.6666666666666665 * 792px), 1px)";
		return e.style.width === "calc(1320px)" ? Math.fround : (x) => x;
	}();
	CharacterType = {
		SPACE: 0,
		ALPHA_LETTER: 1,
		PUNCT: 2,
		HAN_LETTER: 3,
		KATAKANA_LETTER: 4,
		HIRAGANA_LETTER: 5,
		HALFWIDTH_KATAKANA_LETTER: 6,
		THAI_LETTER: 7
	};
	FindState = {
		FOUND: 0,
		NOT_FOUND: 1,
		WRAPPED: 2,
		PENDING: 3
	};
	FIND_TIMEOUT = 250;
	MATCH_SCROLL_OFFSET_TOP = -50;
	MATCH_SCROLL_OFFSET_LEFT = -400;
	CHARACTERS_TO_NORMALIZE = {
		"‐": "-",
		"‘": "'",
		"’": "'",
		"‚": "'",
		"‛": "'",
		"“": "\"",
		"”": "\"",
		"„": "\"",
		"‟": "\"",
		"¼": "1/4",
		"½": "1/2",
		"¾": "3/4"
	};
	DIACRITICS_EXCEPTION = /* @__PURE__ */ new Set([
		12441,
		12442,
		2381,
		2509,
		2637,
		2765,
		2893,
		3021,
		3149,
		3277,
		3387,
		3388,
		3405,
		3530,
		3642,
		3770,
		3972,
		4153,
		4154,
		5908,
		5940,
		6098,
		6752,
		6980,
		7082,
		7083,
		7154,
		7155,
		11647,
		43014,
		43052,
		43204,
		43347,
		43456,
		43766,
		44013,
		3158,
		3953,
		3954,
		3962,
		3963,
		3964,
		3965,
		3968,
		3956
	]);
	DIACRITICS_REG_EXP = /\p{M}+/gu;
	SPECIAL_CHARS_REG_EXP = /([.*+?^${}()|[\]\\])|(\p{P})|(\s+)|(\p{M})|(\p{L})/gu;
	NOT_DIACRITIC_FROM_END_REG_EXP = /([^\p{M}])\p{M}*$/u;
	NOT_DIACRITIC_FROM_START_REG_EXP = /^\p{M}*([^\p{M}])/u;
	SYLLABLES_REG_EXP = /[\uAC00-\uD7AF\uFA6C\uFACF-\uFAD1\uFAD5-\uFAD7]+/g;
	SYLLABLES_LENGTHS = /* @__PURE__ */ new Map();
	FIRST_CHAR_SYLLABLES_REG_EXP = "[\\u1100-\\u1112\\ud7a4-\\ud7af\\ud84a\\ud84c\\ud850\\ud854\\ud857\\ud85f]";
	NFKC_CHARS_TO_NORMALIZE = /* @__PURE__ */ new Map();
	noSyllablesRegExp = null;
	withSyllablesRegExp = null;
	PDFFindController = class {
		#state = null;
		#updateMatchesCountOnProgress = true;
		#visitedPagesCount = 0;
		constructor({ linkService, eventBus, updateMatchesCountOnProgress = true }) {
			this._linkService = linkService;
			this._eventBus = eventBus;
			this.#updateMatchesCountOnProgress = updateMatchesCountOnProgress;
			this.onIsPageVisible = null;
			this.#reset();
			eventBus._on("find", this.#onFind.bind(this));
			eventBus._on("findbarclose", this.#onFindBarClose.bind(this));
		}
		get highlightMatches() {
			return this._highlightMatches;
		}
		get pageMatches() {
			return this._pageMatches;
		}
		get pageMatchesLength() {
			return this._pageMatchesLength;
		}
		get selected() {
			return this._selected;
		}
		get state() {
			return this.#state;
		}
		setDocument(pdfDocument) {
			if (this._pdfDocument) this.#reset();
			if (!pdfDocument) return;
			this._pdfDocument = pdfDocument;
			this._firstPageCapability.resolve();
		}
		#onFind(state) {
			if (!state) return;
			const pdfDocument = this._pdfDocument;
			const { type } = state;
			if (this.#state === null || this.#shouldDirtyMatch(state)) this._dirtyMatch = true;
			this.#state = state;
			if (type !== "highlightallchange") this.#updateUIState(FindState.PENDING);
			this._firstPageCapability.promise.then(() => {
				if (!this._pdfDocument || pdfDocument && this._pdfDocument !== pdfDocument) return;
				this.#extractText();
				const findbarClosed = !this._highlightMatches;
				const pendingTimeout = !!this._findTimeout;
				if (this._findTimeout) {
					clearTimeout(this._findTimeout);
					this._findTimeout = null;
				}
				if (!type) this._findTimeout = setTimeout(() => {
					this.#nextMatch();
					this._findTimeout = null;
				}, FIND_TIMEOUT);
				else if (this._dirtyMatch) this.#nextMatch();
				else if (type === "again") {
					this.#nextMatch();
					if (findbarClosed && this.#state.highlightAll) this.#updateAllPages();
				} else if (type === "highlightallchange") {
					if (pendingTimeout) this.#nextMatch();
					else this._highlightMatches = true;
					this.#updateAllPages();
				} else this.#nextMatch();
			});
		}
		scrollMatchIntoView({ element = null, selectedLeft = 0, pageIndex = -1, matchIndex = -1 }) {
			if (!this._scrollMatches || !element) return;
			else if (matchIndex === -1 || matchIndex !== this._selected.matchIdx) return;
			else if (pageIndex === -1 || pageIndex !== this._selected.pageIdx) return;
			this._scrollMatches = false;
			scrollIntoView(element, {
				top: MATCH_SCROLL_OFFSET_TOP,
				left: selectedLeft + MATCH_SCROLL_OFFSET_LEFT
			}, true);
		}
		#reset() {
			this._highlightMatches = false;
			this._scrollMatches = false;
			this._pdfDocument = null;
			this._pageMatches = [];
			this._pageMatchesLength = [];
			this.#visitedPagesCount = 0;
			this.#state = null;
			this._selected = {
				pageIdx: -1,
				matchIdx: -1
			};
			this._offset = {
				pageIdx: null,
				matchIdx: null,
				wrapped: false
			};
			this._extractTextPromises = [];
			this._pageContents = [];
			this._pageDiffs = [];
			this._hasDiacritics = [];
			this._matchesCountTotal = 0;
			this._pagesToSearch = null;
			this._pendingFindMatches = /* @__PURE__ */ new Set();
			this._resumePageIdx = null;
			this._dirtyMatch = false;
			clearTimeout(this._findTimeout);
			this._findTimeout = null;
			this._firstPageCapability = Promise.withResolvers();
		}
		get #query() {
			const { query } = this.#state;
			if (typeof query === "string") {
				if (query !== this._rawQuery) {
					this._rawQuery = query;
					[this._normalizedQuery] = normalize(query);
				}
				return this._normalizedQuery;
			}
			return (query || []).filter((q) => !!q).map((q) => normalize(q)[0]);
		}
		#shouldDirtyMatch(state) {
			const newQuery = state.query, prevQuery = this.#state.query;
			const newType = typeof newQuery;
			if (newType !== typeof prevQuery) return true;
			if (newType === "string") {
				if (newQuery !== prevQuery) return true;
			} else if (JSON.stringify(newQuery) !== JSON.stringify(prevQuery)) return true;
			switch (state.type) {
				case "again":
					const pageNumber = this._selected.pageIdx + 1;
					const linkService = this._linkService;
					return pageNumber >= 1 && pageNumber <= linkService.pagesCount && pageNumber !== linkService.page && !(this.onIsPageVisible?.(pageNumber) ?? true);
				case "highlightallchange": return false;
			}
			return true;
		}
		#isEntireWord(content, startIdx, length) {
			let match = content.slice(0, startIdx).match(NOT_DIACRITIC_FROM_END_REG_EXP);
			if (match) {
				const first = content.charCodeAt(startIdx);
				const limit = match[1].charCodeAt(0);
				if (getCharacterType(first) === getCharacterType(limit)) return false;
			}
			match = content.slice(startIdx + length).match(NOT_DIACRITIC_FROM_START_REG_EXP);
			if (match) {
				const last = content.charCodeAt(startIdx + length - 1);
				const limit = match[1].charCodeAt(0);
				if (getCharacterType(last) === getCharacterType(limit)) return false;
			}
			return true;
		}
		#convertToRegExpString(query, hasDiacritics) {
			const { matchDiacritics } = this.#state;
			let isUnicode = false;
			query = query.replaceAll(SPECIAL_CHARS_REG_EXP, (match, p1, p2, p3, p4, p5) => {
				if (p1) return `[ ]*\\${p1}[ ]*`;
				if (p2) return `[ ]*${p2}[ ]*`;
				if (p3) return "[ ]+";
				if (matchDiacritics) return p4 || p5;
				if (p4) return DIACRITICS_EXCEPTION.has(p4.charCodeAt(0)) ? p4 : "";
				if (hasDiacritics) {
					isUnicode = true;
					return `${p5}\\p{M}*`;
				}
				return p5;
			});
			if (query.endsWith("[ ]*")) query = query.slice(0, query.length - 4);
			if (matchDiacritics) {
				if (hasDiacritics) {
					DIACRITICS_EXCEPTION_STR ||= String.fromCharCode(...DIACRITICS_EXCEPTION);
					isUnicode = true;
					query = `${query}(?=[${DIACRITICS_EXCEPTION_STR}]|[^\\p{M}]|$)`;
				}
			}
			return [isUnicode, query];
		}
		#calculateMatch(pageIndex) {
			const query = this.#query;
			if (query.length === 0) return;
			const pageContent = this._pageContents[pageIndex];
			const matcherResult = this.match(query, pageContent, pageIndex);
			const matches = this._pageMatches[pageIndex] = [];
			const matchesLength = this._pageMatchesLength[pageIndex] = [];
			const diffs = this._pageDiffs[pageIndex];
			matcherResult?.forEach(({ index, length }) => {
				const [matchPos, matchLen] = getOriginalIndex(diffs, index, length);
				if (matchLen) {
					matches.push(matchPos);
					matchesLength.push(matchLen);
				}
			});
			if (this.#state.highlightAll) this.#updatePage(pageIndex);
			if (this._resumePageIdx === pageIndex) {
				this._resumePageIdx = null;
				this.#nextPageMatch();
			}
			const pageMatchesCount = matches.length;
			this._matchesCountTotal += pageMatchesCount;
			if (this.#updateMatchesCountOnProgress) {
				if (pageMatchesCount > 0) this.#updateUIResultsCount();
			} else if (++this.#visitedPagesCount === this._linkService.pagesCount) this.#updateUIResultsCount();
		}
		match(query, pageContent, pageIndex) {
			const hasDiacritics = this._hasDiacritics[pageIndex];
			let isUnicode = false;
			if (typeof query === "string") [isUnicode, query] = this.#convertToRegExpString(query, hasDiacritics);
			else query = query.sort().reverse().map((q) => {
				const [isUnicodePart, queryPart] = this.#convertToRegExpString(q, hasDiacritics);
				isUnicode ||= isUnicodePart;
				return `(${queryPart})`;
			}).join("|");
			if (!query) return;
			const { caseSensitive, entireWord } = this.#state;
			query = new RegExp(query, `g${isUnicode ? "u" : ""}${caseSensitive ? "" : "i"}`);
			const matches = [];
			let match;
			while ((match = query.exec(pageContent)) !== null) {
				if (entireWord && !this.#isEntireWord(pageContent, match.index, match[0].length)) continue;
				matches.push({
					index: match.index,
					length: match[0].length
				});
			}
			return matches;
		}
		#extractText() {
			if (this._extractTextPromises.length > 0) return;
			let deferred = Promise.resolve();
			const textOptions = { disableNormalization: true };
			for (let i = 0, ii = this._linkService.pagesCount; i < ii; i++) {
				const { promise, resolve } = Promise.withResolvers();
				this._extractTextPromises[i] = promise;
				deferred = deferred.then(() => {
					return this._pdfDocument.getPage(i + 1).then((pdfPage) => pdfPage.getTextContent(textOptions)).then((textContent) => {
						const strBuf = [];
						for (const textItem of textContent.items) {
							strBuf.push(textItem.str);
							if (textItem.hasEOL) strBuf.push("\n");
						}
						[this._pageContents[i], this._pageDiffs[i], this._hasDiacritics[i]] = normalize(strBuf.join(""));
						resolve();
					}, (reason) => {
						console.error(`Unable to get text content for page ${i + 1}`, reason);
						this._pageContents[i] = "";
						this._pageDiffs[i] = null;
						this._hasDiacritics[i] = false;
						resolve();
					});
				});
			}
		}
		#updatePage(index) {
			if (this._scrollMatches && this._selected.pageIdx === index) this._linkService.page = index + 1;
			this._eventBus.dispatch("updatetextlayermatches", {
				source: this,
				pageIndex: index
			});
		}
		#updateAllPages() {
			this._eventBus.dispatch("updatetextlayermatches", {
				source: this,
				pageIndex: -1
			});
		}
		#nextMatch() {
			const previous = this.#state.findPrevious;
			const currentPageIndex = this._linkService.page - 1;
			const numPages = this._linkService.pagesCount;
			this._highlightMatches = true;
			if (this._dirtyMatch) {
				this._dirtyMatch = false;
				this._selected.pageIdx = this._selected.matchIdx = -1;
				this._offset.pageIdx = currentPageIndex;
				this._offset.matchIdx = null;
				this._offset.wrapped = false;
				this._resumePageIdx = null;
				this._pageMatches.length = 0;
				this._pageMatchesLength.length = 0;
				this.#visitedPagesCount = 0;
				this._matchesCountTotal = 0;
				this.#updateAllPages();
				for (let i = 0; i < numPages; i++) {
					if (this._pendingFindMatches.has(i)) continue;
					this._pendingFindMatches.add(i);
					this._extractTextPromises[i].then(() => {
						this._pendingFindMatches.delete(i);
						this.#calculateMatch(i);
					});
				}
			}
			if (this.#query.length === 0) {
				this.#updateUIState(FindState.FOUND);
				return;
			}
			if (this._resumePageIdx) return;
			const offset = this._offset;
			this._pagesToSearch = numPages;
			if (offset.matchIdx !== null) {
				const numPageMatches = this._pageMatches[offset.pageIdx].length;
				if (!previous && offset.matchIdx + 1 < numPageMatches || previous && offset.matchIdx > 0) {
					offset.matchIdx = previous ? offset.matchIdx - 1 : offset.matchIdx + 1;
					this.#updateMatch(true);
					return;
				}
				this.#advanceOffsetPage(previous);
			}
			this.#nextPageMatch();
		}
		#matchesReady(matches) {
			const offset = this._offset;
			const numMatches = matches.length;
			const previous = this.#state.findPrevious;
			if (numMatches) {
				offset.matchIdx = previous ? numMatches - 1 : 0;
				this.#updateMatch(true);
				return true;
			}
			this.#advanceOffsetPage(previous);
			if (offset.wrapped) {
				offset.matchIdx = null;
				if (this._pagesToSearch < 0) {
					this.#updateMatch(false);
					return true;
				}
			}
			return false;
		}
		#nextPageMatch() {
			if (this._resumePageIdx !== null) console.error("There can only be one pending page.");
			let matches = null;
			do {
				const pageIdx = this._offset.pageIdx;
				matches = this._pageMatches[pageIdx];
				if (!matches) {
					this._resumePageIdx = pageIdx;
					break;
				}
			} while (!this.#matchesReady(matches));
		}
		#advanceOffsetPage(previous) {
			const offset = this._offset;
			const numPages = this._linkService.pagesCount;
			offset.pageIdx = previous ? offset.pageIdx - 1 : offset.pageIdx + 1;
			offset.matchIdx = null;
			this._pagesToSearch--;
			if (offset.pageIdx >= numPages || offset.pageIdx < 0) {
				offset.pageIdx = previous ? numPages - 1 : 0;
				offset.wrapped = true;
			}
		}
		#updateMatch(found = false) {
			let state = FindState.NOT_FOUND;
			const wrapped = this._offset.wrapped;
			this._offset.wrapped = false;
			if (found) {
				const previousPage = this._selected.pageIdx;
				this._selected.pageIdx = this._offset.pageIdx;
				this._selected.matchIdx = this._offset.matchIdx;
				state = wrapped ? FindState.WRAPPED : FindState.FOUND;
				if (previousPage !== -1 && previousPage !== this._selected.pageIdx) this.#updatePage(previousPage);
			}
			this.#updateUIState(state, this.#state.findPrevious);
			if (this._selected.pageIdx !== -1) {
				this._scrollMatches = true;
				this.#updatePage(this._selected.pageIdx);
			}
		}
		#onFindBarClose(evt) {
			const pdfDocument = this._pdfDocument;
			this._firstPageCapability.promise.then(() => {
				if (!this._pdfDocument || pdfDocument && this._pdfDocument !== pdfDocument) return;
				if (this._findTimeout) {
					clearTimeout(this._findTimeout);
					this._findTimeout = null;
				}
				if (this._resumePageIdx) {
					this._resumePageIdx = null;
					this._dirtyMatch = true;
				}
				this.#updateUIState(FindState.FOUND);
				this._highlightMatches = false;
				this.#updateAllPages();
			});
		}
		#requestMatchesCount() {
			const { pageIdx, matchIdx } = this._selected;
			let current = 0, total = this._matchesCountTotal;
			if (matchIdx !== -1) {
				for (let i = 0; i < pageIdx; i++) current += this._pageMatches[i]?.length || 0;
				current += matchIdx + 1;
			}
			if (current < 1 || current > total) current = total = 0;
			return {
				current,
				total
			};
		}
		#updateUIResultsCount() {
			this._eventBus.dispatch("updatefindmatchescount", {
				source: this,
				matchesCount: this.#requestMatchesCount()
			});
		}
		#updateUIState(state, previous = false) {
			if (!this.#updateMatchesCountOnProgress && (this.#visitedPagesCount !== this._linkService.pagesCount || state === FindState.PENDING)) return;
			this._eventBus.dispatch("updatefindcontrolstate", {
				source: this,
				state,
				previous,
				entireWord: this.#state?.entireWord ?? null,
				matchesCount: this.#requestMatchesCount(),
				rawQuery: this.#state?.query ?? null
			});
		}
	};
	DEFAULT_LINK_REL = "noopener noreferrer nofollow";
	LinkTarget = {
		NONE: 0,
		SELF: 1,
		BLANK: 2,
		PARENT: 3,
		TOP: 4
	};
	PDFLinkService$1 = class PDFLinkService$1 {
		externalLinkEnabled = true;
		constructor({ eventBus, externalLinkTarget = null, externalLinkRel = null, ignoreDestinationZoom = false } = {}) {
			this.eventBus = eventBus;
			this.externalLinkTarget = externalLinkTarget;
			this.externalLinkRel = externalLinkRel;
			this._ignoreDestinationZoom = ignoreDestinationZoom;
			this.baseUrl = null;
			this.pdfDocument = null;
			this.pdfViewer = null;
			this.pdfHistory = null;
		}
		setDocument(pdfDocument, baseUrl = null) {
			this.baseUrl = baseUrl;
			this.pdfDocument = pdfDocument;
		}
		setViewer(pdfViewer) {
			this.pdfViewer = pdfViewer;
		}
		setHistory(pdfHistory) {
			this.pdfHistory = pdfHistory;
		}
		get pagesCount() {
			return this.pdfDocument ? this.pdfDocument.numPages : 0;
		}
		get page() {
			return this.pdfDocument ? this.pdfViewer.currentPageNumber : 1;
		}
		set page(value) {
			if (this.pdfDocument) this.pdfViewer.currentPageNumber = value;
		}
		get rotation() {
			return this.pdfDocument ? this.pdfViewer.pagesRotation : 0;
		}
		set rotation(value) {
			if (this.pdfDocument) this.pdfViewer.pagesRotation = value;
		}
		get isInPresentationMode() {
			return this.pdfDocument ? this.pdfViewer.isInPresentationMode : false;
		}
		async goToDestination(dest) {
			if (!this.pdfDocument) return;
			let namedDest, explicitDest, pageNumber;
			if (typeof dest === "string") {
				namedDest = dest;
				explicitDest = await this.pdfDocument.getDestination(dest);
			} else {
				namedDest = null;
				explicitDest = await dest;
			}
			if (!Array.isArray(explicitDest)) {
				console.error(`goToDestination: "${explicitDest}" is not a valid destination array, for dest="${dest}".`);
				return;
			}
			const [destRef] = explicitDest;
			if (destRef && typeof destRef === "object") {
				pageNumber = this.pdfDocument.cachedPageNumber(destRef);
				if (!pageNumber) try {
					pageNumber = await this.pdfDocument.getPageIndex(destRef) + 1;
				} catch {
					console.error(`goToDestination: "${destRef}" is not a valid page reference, for dest="${dest}".`);
					return;
				}
			} else if (Number.isInteger(destRef)) pageNumber = destRef + 1;
			if (!pageNumber || pageNumber < 1 || pageNumber > this.pagesCount) {
				console.error(`goToDestination: "${pageNumber}" is not a valid page number, for dest="${dest}".`);
				return;
			}
			if (this.pdfHistory) {
				this.pdfHistory.pushCurrentPosition();
				this.pdfHistory.push({
					namedDest,
					explicitDest,
					pageNumber
				});
			}
			this.pdfViewer.scrollPageIntoView({
				pageNumber,
				destArray: explicitDest,
				ignoreDestinationZoom: this._ignoreDestinationZoom
			});
		}
		goToPage(val) {
			if (!this.pdfDocument) return;
			const pageNumber = typeof val === "string" && this.pdfViewer.pageLabelToPageNumber(val) || val | 0;
			if (!(Number.isInteger(pageNumber) && pageNumber > 0 && pageNumber <= this.pagesCount)) {
				console.error(`PDFLinkService.goToPage: "${val}" is not a valid page.`);
				return;
			}
			if (this.pdfHistory) {
				this.pdfHistory.pushCurrentPosition();
				this.pdfHistory.pushPage(pageNumber);
			}
			this.pdfViewer.scrollPageIntoView({ pageNumber });
		}
		addLinkAttributes(link, url, newWindow = false) {
			if (!url || typeof url !== "string") throw new Error("A valid \"url\" parameter must provided.");
			const target = newWindow ? LinkTarget.BLANK : this.externalLinkTarget, rel = this.externalLinkRel;
			if (this.externalLinkEnabled) link.href = link.title = url;
			else {
				link.href = "";
				link.title = `Disabled: ${url}`;
				link.onclick = () => false;
			}
			let targetStr = "";
			switch (target) {
				case LinkTarget.NONE: break;
				case LinkTarget.SELF:
					targetStr = "_self";
					break;
				case LinkTarget.BLANK:
					targetStr = "_blank";
					break;
				case LinkTarget.PARENT:
					targetStr = "_parent";
					break;
				case LinkTarget.TOP: targetStr = "_top";
			}
			link.target = targetStr;
			link.rel = typeof rel === "string" ? rel : DEFAULT_LINK_REL;
		}
		getDestinationHash(dest) {
			if (typeof dest === "string") {
				if (dest.length > 0) return this.getAnchorUrl("#" + escape(dest));
			} else if (Array.isArray(dest)) {
				const str = JSON.stringify(dest);
				if (str.length > 0) return this.getAnchorUrl("#" + escape(str));
			}
			return this.getAnchorUrl("");
		}
		getAnchorUrl(anchor) {
			return this.baseUrl ? this.baseUrl + anchor : anchor;
		}
		setHash(hash) {
			if (!this.pdfDocument) return;
			let pageNumber, dest;
			if (hash.includes("=")) {
				const params = parseQueryString(hash);
				if (params.has("search")) {
					const query = params.get("search").replaceAll("\"", ""), phrase = params.get("phrase") === "true";
					this.eventBus.dispatch("findfromurlhash", {
						source: this,
						query: phrase ? query : query.match(/\S+/g)
					});
				}
				if (params.has("page")) pageNumber = params.get("page") | 0 || 1;
				if (params.has("zoom")) {
					const zoomArgs = params.get("zoom").split(",");
					const zoomArg = zoomArgs[0];
					const zoomArgNumber = parseFloat(zoomArg);
					if (!zoomArg.includes("Fit")) dest = [
						null,
						{ name: "XYZ" },
						zoomArgs.length > 1 ? zoomArgs[1] | 0 : null,
						zoomArgs.length > 2 ? zoomArgs[2] | 0 : null,
						zoomArgNumber ? zoomArgNumber / 100 : zoomArg
					];
					else if (zoomArg === "Fit" || zoomArg === "FitB") dest = [null, { name: zoomArg }];
					else if (zoomArg === "FitH" || zoomArg === "FitBH" || zoomArg === "FitV" || zoomArg === "FitBV") dest = [
						null,
						{ name: zoomArg },
						zoomArgs.length > 1 ? zoomArgs[1] | 0 : null
					];
					else if (zoomArg === "FitR") {
						if (zoomArgs.length !== 5) console.error("PDFLinkService.setHash: Not enough parameters for \"FitR\".");
						else dest = [
							null,
							{ name: zoomArg },
							zoomArgs[1] | 0,
							zoomArgs[2] | 0,
							zoomArgs[3] | 0,
							zoomArgs[4] | 0
						];
					} else console.error(`PDFLinkService.setHash: "${zoomArg}" is not a valid zoom value.`);
				}
				if (dest) this.pdfViewer.scrollPageIntoView({
					pageNumber: pageNumber || this.page,
					destArray: dest,
					allowNegativeOffset: true
				});
				else if (pageNumber) this.page = pageNumber;
				if (params.has("pagemode")) this.eventBus.dispatch("pagemode", {
					source: this,
					mode: params.get("pagemode")
				});
				if (params.has("nameddest")) this.goToDestination(params.get("nameddest"));
				return;
			}
			dest = unescape(hash);
			try {
				dest = JSON.parse(dest);
				if (!Array.isArray(dest)) dest = dest.toString();
			} catch {}
			if (typeof dest === "string" || PDFLinkService$1.#isValidExplicitDest(dest)) {
				this.goToDestination(dest);
				return;
			}
			console.error(`PDFLinkService.setHash: "${unescape(hash)}" is not a valid destination.`);
		}
		executeNamedAction(action) {
			if (!this.pdfDocument) return;
			switch (action) {
				case "GoBack":
					this.pdfHistory?.back();
					break;
				case "GoForward":
					this.pdfHistory?.forward();
					break;
				case "NextPage":
					this.pdfViewer.nextPage();
					break;
				case "PrevPage":
					this.pdfViewer.previousPage();
					break;
				case "LastPage":
					this.page = this.pagesCount;
					break;
				case "FirstPage": this.page = 1;
			}
			this.eventBus.dispatch("namedaction", {
				source: this,
				action
			});
		}
		async executeSetOCGState(action) {
			if (!this.pdfDocument) return;
			const pdfDocument = this.pdfDocument, optionalContentConfig = await this.pdfViewer.optionalContentConfigPromise;
			if (pdfDocument !== this.pdfDocument) return;
			optionalContentConfig.setOCGState(action);
			this.pdfViewer.optionalContentConfigPromise = Promise.resolve(optionalContentConfig);
		}
		static #isValidExplicitDest(dest) {
			if (!Array.isArray(dest) || dest.length < 2) return false;
			const [page, zoom, ...args] = dest;
			if (!(typeof page === "object" && Number.isInteger(page?.num) && Number.isInteger(page?.gen)) && !Number.isInteger(page)) return false;
			if (!(typeof zoom === "object" && typeof zoom?.name === "string")) return false;
			const argsLen = args.length;
			let allowNull = true;
			switch (zoom.name) {
				case "XYZ":
					if (argsLen < 2 || argsLen > 3) return false;
					break;
				case "Fit":
				case "FitB": return argsLen === 0;
				case "FitH":
				case "FitBH":
				case "FitV":
				case "FitBV":
					if (argsLen > 1) return false;
					break;
				case "FitR":
					if (argsLen !== 4) return false;
					allowNull = false;
					break;
				default: return false;
			}
			for (const arg of args) if (!(typeof arg === "number" || allowNull && arg === null)) return false;
			return true;
		}
	};
	SimpleLinkService = class extends PDFLinkService$1 {
		setDocument(pdfDocument, baseUrl = null) {}
	};
	({AbortException, AnnotationEditorLayer, AnnotationEditorParamsType, AnnotationEditorType, AnnotationEditorUIManager, AnnotationLayer, AnnotationMode, build, ColorPicker, createValidAbsoluteUrl, DOMSVGFactory, DrawLayer, FeatureTest, fetchData, getDocument: getDocument$1, getFilenameFromUrl, getPdfFilenameFromUrl, getXfaPageViewport, GlobalWorkerOptions: GlobalWorkerOptions$1, ImageKind, InvalidPDFException, isDataScheme, isPdfFile, MissingPDFException, noContextMenu, normalizeUnicode, OPS, OutputScale, PasswordResponses, PDFDataRangeTransport, PDFDateString, PDFWorker, PermissionFlag, PixelsPerInch, RenderingCancelledException, setLayerDimensions, shadow, stopEvent, TextLayer, TouchManager, UnexpectedResponseException, Util, VerbosityLevel, version: version$1, XfaLayer} = globalThis.pdfjsLib);
	AnnotationLayerBuilder = class {
		#onAppend = null;
		#eventAbortController = null;
		constructor({ pdfPage, linkService, downloadManager, annotationStorage = null, imageResourcesPath = "", renderForms = true, enableScripting = false, hasJSActionsPromise = null, fieldObjectsPromise = null, annotationCanvasMap = null, accessibilityManager = null, annotationEditorUIManager = null, onAppend = null }) {
			this.pdfPage = pdfPage;
			this.linkService = linkService;
			this.downloadManager = downloadManager;
			this.imageResourcesPath = imageResourcesPath;
			this.renderForms = renderForms;
			this.annotationStorage = annotationStorage;
			this.enableScripting = enableScripting;
			this._hasJSActionsPromise = hasJSActionsPromise || Promise.resolve(false);
			this._fieldObjectsPromise = fieldObjectsPromise || Promise.resolve(null);
			this._annotationCanvasMap = annotationCanvasMap;
			this._accessibilityManager = accessibilityManager;
			this._annotationEditorUIManager = annotationEditorUIManager;
			this.#onAppend = onAppend;
			this.annotationLayer = null;
			this.div = null;
			this._cancelled = false;
			this._eventBus = linkService.eventBus;
		}
		async render(viewport, options, intent = "display") {
			if (this.div) {
				if (this._cancelled || !this.annotationLayer) return;
				this.annotationLayer.update({ viewport: viewport.clone({ dontFlip: true }) });
				return;
			}
			const [annotations, hasJSActions, fieldObjects] = await Promise.all([
				this.pdfPage.getAnnotations({ intent }),
				this._hasJSActionsPromise,
				this._fieldObjectsPromise
			]);
			if (this._cancelled) return;
			const div = this.div = document.createElement("div");
			div.className = "annotationLayer";
			this.#onAppend?.(div);
			if (annotations.length === 0) {
				this.hide();
				return;
			}
			this.annotationLayer = new AnnotationLayer({
				div,
				accessibilityManager: this._accessibilityManager,
				annotationCanvasMap: this._annotationCanvasMap,
				annotationEditorUIManager: this._annotationEditorUIManager,
				page: this.pdfPage,
				viewport: viewport.clone({ dontFlip: true }),
				structTreeLayer: options?.structTreeLayer || null
			});
			await this.annotationLayer.render({
				annotations,
				imageResourcesPath: this.imageResourcesPath,
				renderForms: this.renderForms,
				linkService: this.linkService,
				downloadManager: this.downloadManager,
				annotationStorage: this.annotationStorage,
				enableScripting: this.enableScripting,
				hasJSActions,
				fieldObjects
			});
			if (this.linkService.isInPresentationMode) this.#updatePresentationModeState(PresentationModeState.FULLSCREEN);
			if (!this.#eventAbortController) {
				this.#eventAbortController = new AbortController();
				this._eventBus?._on("presentationmodechanged", (evt) => {
					this.#updatePresentationModeState(evt.state);
				}, { signal: this.#eventAbortController.signal });
			}
		}
		cancel() {
			this._cancelled = true;
			this.#eventAbortController?.abort();
			this.#eventAbortController = null;
		}
		hide() {
			if (!this.div) return;
			this.div.hidden = true;
		}
		hasEditableAnnotations() {
			return !!this.annotationLayer?.hasEditableAnnotations();
		}
		#updatePresentationModeState(state) {
			if (!this.div) return;
			let disableFormElements = false;
			switch (state) {
				case PresentationModeState.FULLSCREEN:
					disableFormElements = true;
					break;
				case PresentationModeState.NORMAL: break;
				default: return;
			}
			for (const section of this.div.childNodes) {
				if (section.hasAttribute("data-internal-link")) continue;
				section.inert = disableFormElements;
			}
		}
	};
	DownloadManager = class {
		#openBlobUrls = /* @__PURE__ */ new WeakMap();
		downloadData(data, filename, contentType) {
			download(URL.createObjectURL(new Blob([data], { type: contentType })), filename);
		}
		openOrDownloadData(data, filename, dest = null) {
			const contentType = isPdfFile(filename) ? "application/pdf" : "";
			this.downloadData(data, filename, contentType);
			return false;
		}
		download(data, url, filename) {
			let blobUrl;
			if (data) blobUrl = URL.createObjectURL(new Blob([data], { type: "application/pdf" }));
			else {
				if (!createValidAbsoluteUrl(url, "http://example.com")) {
					console.error(`download - not a valid URL: ${url}`);
					return;
				}
				blobUrl = url + "#pdfjs.action=download";
			}
			download(blobUrl, filename);
		}
	};
	WaitOnType = {
		EVENT: "event",
		TIMEOUT: "timeout"
	};
	EventBus$1 = class {
		#listeners = Object.create(null);
		on(eventName, listener, options = null) {
			this._on(eventName, listener, {
				external: true,
				once: options?.once,
				signal: options?.signal
			});
		}
		off(eventName, listener, options = null) {
			this._off(eventName, listener);
		}
		dispatch(eventName, data) {
			const eventListeners = this.#listeners[eventName];
			if (!eventListeners || eventListeners.length === 0) return;
			let externalListeners;
			for (const { listener, external, once } of eventListeners.slice(0)) {
				if (once) this._off(eventName, listener);
				if (external) {
					(externalListeners ||= []).push(listener);
					continue;
				}
				listener(data);
			}
			if (externalListeners) {
				for (const listener of externalListeners) listener(data);
				externalListeners = null;
			}
		}
		_on(eventName, listener, options = null) {
			let rmAbort = null;
			if (options?.signal instanceof AbortSignal) {
				const { signal } = options;
				if (signal.aborted) {
					console.error("Cannot use an `aborted` signal.");
					return;
				}
				const onAbort = () => this._off(eventName, listener);
				rmAbort = () => signal.removeEventListener("abort", onAbort);
				signal.addEventListener("abort", onAbort);
			}
			(this.#listeners[eventName] ||= []).push({
				listener,
				external: options?.external === true,
				once: options?.once === true,
				rmAbort
			});
		}
		_off(eventName, listener, options = null) {
			const eventListeners = this.#listeners[eventName];
			if (!eventListeners) return;
			for (let i = 0, ii = eventListeners.length; i < ii; i++) {
				const evt = eventListeners[i];
				if (evt.listener === listener) {
					evt.rmAbort?.();
					eventListeners.splice(i, 1);
					return;
				}
			}
		}
	};
	FluentType = class {
		constructor(value) {
			this.value = value;
		}
		valueOf() {
			return this.value;
		}
	};
	FluentNone = class extends FluentType {
		constructor(value = "???") {
			super(value);
		}
		toString(scope) {
			return `{${this.value}}`;
		}
	};
	FluentNumber = class extends FluentType {
		constructor(value, opts = {}) {
			super(value);
			this.opts = opts;
		}
		toString(scope) {
			try {
				return scope.memoizeIntlObject(Intl.NumberFormat, this.opts).format(this.value);
			} catch (err) {
				scope.reportError(err);
				return this.value.toString(10);
			}
		}
	};
	FluentDateTime = class extends FluentType {
		constructor(value, opts = {}) {
			super(value);
			this.opts = opts;
		}
		toString(scope) {
			try {
				return scope.memoizeIntlObject(Intl.DateTimeFormat, this.opts).format(this.value);
			} catch (err) {
				scope.reportError(err);
				return new Date(this.value).toISOString();
			}
		}
	};
	MAX_PLACEABLES = 100;
	FSI = "⁨";
	PDI = "⁩";
	Scope = class {
		constructor(bundle, errors, args) {
			this.dirty = /* @__PURE__ */ new WeakSet();
			this.params = null;
			this.placeables = 0;
			this.bundle = bundle;
			this.errors = errors;
			this.args = args;
		}
		reportError(error) {
			if (!this.errors || !(error instanceof Error)) throw error;
			this.errors.push(error);
		}
		memoizeIntlObject(ctor, opts) {
			let cache = this.bundle._intls.get(ctor);
			if (!cache) {
				cache = {};
				this.bundle._intls.set(ctor, cache);
			}
			let id = JSON.stringify(opts);
			if (!cache[id]) cache[id] = new ctor(this.bundle.locales, opts);
			return cache[id];
		}
	};
	NUMBER_ALLOWED = [
		"unitDisplay",
		"currencyDisplay",
		"useGrouping",
		"minimumIntegerDigits",
		"minimumFractionDigits",
		"maximumFractionDigits",
		"minimumSignificantDigits",
		"maximumSignificantDigits"
	];
	DATETIME_ALLOWED = [
		"dateStyle",
		"timeStyle",
		"fractionalSecondDigits",
		"dayPeriod",
		"hour12",
		"weekday",
		"era",
		"year",
		"month",
		"day",
		"hour",
		"minute",
		"second",
		"timeZoneName"
	];
	cache = /* @__PURE__ */ new Map();
	FluentBundle = class {
		constructor(locales, { functions, useIsolating = true, transform = (v) => v } = {}) {
			this._terms = /* @__PURE__ */ new Map();
			this._messages = /* @__PURE__ */ new Map();
			this.locales = Array.isArray(locales) ? locales : [locales];
			this._functions = {
				NUMBER,
				DATETIME,
				...functions
			};
			this._useIsolating = useIsolating;
			this._transform = transform;
			this._intls = getMemoizerForLocale(locales);
		}
		hasMessage(id) {
			return this._messages.has(id);
		}
		getMessage(id) {
			return this._messages.get(id);
		}
		addResource(res, { allowOverrides = false } = {}) {
			const errors = [];
			for (let i = 0; i < res.body.length; i++) {
				let entry = res.body[i];
				if (entry.id.startsWith("-")) {
					if (allowOverrides === false && this._terms.has(entry.id)) {
						errors.push(/* @__PURE__ */ new Error(`Attempt to override an existing term: "${entry.id}"`));
						continue;
					}
					this._terms.set(entry.id, entry);
				} else {
					if (allowOverrides === false && this._messages.has(entry.id)) {
						errors.push(/* @__PURE__ */ new Error(`Attempt to override an existing message: "${entry.id}"`));
						continue;
					}
					this._messages.set(entry.id, entry);
				}
			}
			return errors;
		}
		formatPattern(pattern, args = null, errors = null) {
			if (typeof pattern === "string") return this._transform(pattern);
			let scope = new Scope(this, errors, args);
			try {
				return resolveComplexPattern(scope, pattern).toString(scope);
			} catch (err) {
				if (scope.errors && err instanceof Error) {
					scope.errors.push(err);
					return new FluentNone().toString(scope);
				}
				throw err;
			}
		}
	};
	RE_MESSAGE_START = /^(-?[a-zA-Z][\w-]*) *= */gm;
	RE_ATTRIBUTE_START = /\.([a-zA-Z][\w-]*) *= */y;
	RE_VARIANT_START = /\*?\[/y;
	RE_NUMBER_LITERAL = /(-?[0-9]+(?:\.([0-9]+))?)/y;
	RE_IDENTIFIER = /([a-zA-Z][\w-]*)/y;
	RE_REFERENCE = /([$-])?([a-zA-Z][\w-]*)(?:\.([a-zA-Z][\w-]*))?/y;
	RE_FUNCTION_NAME = /^[A-Z][A-Z0-9_-]*$/;
	RE_TEXT_RUN = /([^{}\n\r]+)/y;
	RE_STRING_RUN = /([^\\"\n\r]*)/y;
	RE_STRING_ESCAPE = /\\([\\"])/y;
	RE_UNICODE_ESCAPE = /\\u([a-fA-F0-9]{4})|\\U([a-fA-F0-9]{6})/y;
	RE_LEADING_NEWLINES = /^\n+/;
	RE_TRAILING_SPACES = / +$/;
	RE_BLANK_LINES = / *\r?\n/g;
	RE_INDENT = /( *)$/;
	TOKEN_BRACE_OPEN = /{\s*/y;
	TOKEN_BRACE_CLOSE = /\s*}/y;
	TOKEN_BRACKET_OPEN = /\[\s*/y;
	TOKEN_BRACKET_CLOSE = /\s*] */y;
	TOKEN_PAREN_OPEN = /\s*\(\s*/y;
	TOKEN_ARROW = /\s*->\s*/y;
	TOKEN_COLON = /\s*:\s*/y;
	TOKEN_COMMA = /\s*,?\s*/y;
	TOKEN_BLANK = /\s+/y;
	FluentResource = class {
		constructor(source) {
			this.body = [];
			RE_MESSAGE_START.lastIndex = 0;
			let cursor = 0;
			while (true) {
				let next = RE_MESSAGE_START.exec(source);
				if (next === null) break;
				cursor = RE_MESSAGE_START.lastIndex;
				try {
					this.body.push(parseMessage(next[1]));
				} catch (err) {
					if (err instanceof SyntaxError) continue;
					throw err;
				}
			}
			function test(re) {
				re.lastIndex = cursor;
				return re.test(source);
			}
			function consumeChar(char, errorClass) {
				if (source[cursor] === char) {
					cursor++;
					return true;
				}
				if (errorClass) throw new errorClass(`Expected ${char}`);
				return false;
			}
			function consumeToken(re, errorClass) {
				if (test(re)) {
					cursor = re.lastIndex;
					return true;
				}
				if (errorClass) throw new errorClass(`Expected ${re.toString()}`);
				return false;
			}
			function match(re) {
				re.lastIndex = cursor;
				let result = re.exec(source);
				if (result === null) throw new SyntaxError(`Expected ${re.toString()}`);
				cursor = re.lastIndex;
				return result;
			}
			function match1(re) {
				return match(re)[1];
			}
			function parseMessage(id) {
				let value = parsePattern();
				let attributes = parseAttributes();
				if (value === null && Object.keys(attributes).length === 0) throw new SyntaxError("Expected message value or attributes");
				return {
					id,
					value,
					attributes
				};
			}
			function parseAttributes() {
				let attrs = Object.create(null);
				while (test(RE_ATTRIBUTE_START)) {
					let name = match1(RE_ATTRIBUTE_START);
					let value = parsePattern();
					if (value === null) throw new SyntaxError("Expected attribute value");
					attrs[name] = value;
				}
				return attrs;
			}
			function parsePattern() {
				let first;
				if (test(RE_TEXT_RUN)) first = match1(RE_TEXT_RUN);
				if (source[cursor] === "{" || source[cursor] === "}") return parsePatternElements(first ? [first] : [], Infinity);
				let indent = parseIndent();
				if (indent) {
					if (first) return parsePatternElements([first, indent], indent.length);
					indent.value = trim(indent.value, RE_LEADING_NEWLINES);
					return parsePatternElements([indent], indent.length);
				}
				if (first) return trim(first, RE_TRAILING_SPACES);
				return null;
			}
			function parsePatternElements(elements = [], commonIndent) {
				while (true) {
					if (test(RE_TEXT_RUN)) {
						elements.push(match1(RE_TEXT_RUN));
						continue;
					}
					if (source[cursor] === "{") {
						elements.push(parsePlaceable());
						continue;
					}
					if (source[cursor] === "}") throw new SyntaxError("Unbalanced closing brace");
					let indent = parseIndent();
					if (indent) {
						elements.push(indent);
						commonIndent = Math.min(commonIndent, indent.length);
						continue;
					}
					break;
				}
				let lastIndex = elements.length - 1;
				let lastElement = elements[lastIndex];
				if (typeof lastElement === "string") elements[lastIndex] = trim(lastElement, RE_TRAILING_SPACES);
				let baked = [];
				for (let element of elements) {
					if (element instanceof Indent) element = element.value.slice(0, element.value.length - commonIndent);
					if (element) baked.push(element);
				}
				return baked;
			}
			function parsePlaceable() {
				consumeToken(TOKEN_BRACE_OPEN, SyntaxError);
				let selector = parseInlineExpression();
				if (consumeToken(TOKEN_BRACE_CLOSE)) return selector;
				if (consumeToken(TOKEN_ARROW)) {
					let variants = parseVariants();
					consumeToken(TOKEN_BRACE_CLOSE, SyntaxError);
					return {
						type: "select",
						selector,
						...variants
					};
				}
				throw new SyntaxError("Unclosed placeable");
			}
			function parseInlineExpression() {
				if (source[cursor] === "{") return parsePlaceable();
				if (test(RE_REFERENCE)) {
					let [, sigil, name, attr = null] = match(RE_REFERENCE);
					if (sigil === "$") return {
						type: "var",
						name
					};
					if (consumeToken(TOKEN_PAREN_OPEN)) {
						let args = parseArguments();
						if (sigil === "-") return {
							type: "term",
							name,
							attr,
							args
						};
						if (RE_FUNCTION_NAME.test(name)) return {
							type: "func",
							name,
							args
						};
						throw new SyntaxError("Function names must be all upper-case");
					}
					if (sigil === "-") return {
						type: "term",
						name,
						attr,
						args: []
					};
					return {
						type: "mesg",
						name,
						attr
					};
				}
				return parseLiteral();
			}
			function parseArguments() {
				let args = [];
				while (true) {
					switch (source[cursor]) {
						case ")":
							cursor++;
							return args;
						case void 0: throw new SyntaxError("Unclosed argument list");
					}
					args.push(parseArgument());
					consumeToken(TOKEN_COMMA);
				}
			}
			function parseArgument() {
				let expr = parseInlineExpression();
				if (expr.type !== "mesg") return expr;
				if (consumeToken(TOKEN_COLON)) return {
					type: "narg",
					name: expr.name,
					value: parseLiteral()
				};
				return expr;
			}
			function parseVariants() {
				let variants = [];
				let count = 0;
				let star;
				while (test(RE_VARIANT_START)) {
					if (consumeChar("*")) star = count;
					let key = parseVariantKey();
					let value = parsePattern();
					if (value === null) throw new SyntaxError("Expected variant value");
					variants[count++] = {
						key,
						value
					};
				}
				if (count === 0) return null;
				if (star === void 0) throw new SyntaxError("Expected default variant");
				return {
					variants,
					star
				};
			}
			function parseVariantKey() {
				consumeToken(TOKEN_BRACKET_OPEN, SyntaxError);
				let key;
				if (test(RE_NUMBER_LITERAL)) key = parseNumberLiteral();
				else key = {
					type: "str",
					value: match1(RE_IDENTIFIER)
				};
				consumeToken(TOKEN_BRACKET_CLOSE, SyntaxError);
				return key;
			}
			function parseLiteral() {
				if (test(RE_NUMBER_LITERAL)) return parseNumberLiteral();
				if (source[cursor] === "\"") return parseStringLiteral();
				throw new SyntaxError("Invalid expression");
			}
			function parseNumberLiteral() {
				let [, value, fraction = ""] = match(RE_NUMBER_LITERAL);
				let precision = fraction.length;
				return {
					type: "num",
					value: parseFloat(value),
					precision
				};
			}
			function parseStringLiteral() {
				consumeChar("\"", SyntaxError);
				let value = "";
				while (true) {
					value += match1(RE_STRING_RUN);
					if (source[cursor] === "\\") {
						value += parseEscapeSequence();
						continue;
					}
					if (consumeChar("\"")) return {
						type: "str",
						value
					};
					throw new SyntaxError("Unclosed string literal");
				}
			}
			function parseEscapeSequence() {
				if (test(RE_STRING_ESCAPE)) return match1(RE_STRING_ESCAPE);
				if (test(RE_UNICODE_ESCAPE)) {
					let [, codepoint4, codepoint6] = match(RE_UNICODE_ESCAPE);
					let codepoint = parseInt(codepoint4 || codepoint6, 16);
					return codepoint <= 55295 || 57344 <= codepoint ? String.fromCodePoint(codepoint) : "�";
				}
				throw new SyntaxError("Unknown escape sequence");
			}
			function parseIndent() {
				let start = cursor;
				consumeToken(TOKEN_BLANK);
				switch (source[cursor]) {
					case ".":
					case "[":
					case "*":
					case "}":
					case void 0: return false;
					case "{": return makeIndent(source.slice(start, cursor));
				}
				if (source[cursor - 1] === " ") return makeIndent(source.slice(start, cursor));
				return false;
			}
			function trim(text, re) {
				return text.replace(re, "");
			}
			function makeIndent(blank) {
				let value = blank.replace(RE_BLANK_LINES, "\n");
				let length = RE_INDENT.exec(blank)[1].length;
				return new Indent(value, length);
			}
		}
	};
	Indent = class {
		constructor(value, length) {
			this.value = value;
			this.length = length;
		}
	};
	reOverlay = /<|&#?\w+;/;
	TEXT_LEVEL_ELEMENTS = { "http://www.w3.org/1999/xhtml": [
		"em",
		"strong",
		"small",
		"s",
		"cite",
		"q",
		"dfn",
		"abbr",
		"data",
		"time",
		"code",
		"var",
		"samp",
		"kbd",
		"sub",
		"sup",
		"i",
		"b",
		"u",
		"mark",
		"bdi",
		"bdo",
		"span",
		"br",
		"wbr"
	] };
	LOCALIZABLE_ATTRIBUTES = {
		"http://www.w3.org/1999/xhtml": {
			global: [
				"title",
				"aria-label",
				"aria-valuetext"
			],
			a: ["download"],
			area: ["download", "alt"],
			input: ["alt", "placeholder"],
			menuitem: ["label"],
			menu: ["label"],
			optgroup: ["label"],
			option: ["label"],
			track: ["label"],
			img: ["alt"],
			textarea: ["placeholder"],
			th: ["abbr"]
		},
		"http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul": {
			global: [
				"accesskey",
				"aria-label",
				"aria-valuetext",
				"label",
				"title",
				"tooltiptext"
			],
			description: ["value"],
			key: ["key", "keycode"],
			label: ["value"],
			textbox: ["placeholder", "value"]
		}
	};
	CachedIterable = class extends Array {
		static from(iterable) {
			if (iterable instanceof this) return iterable;
			return new this(iterable);
		}
	};
	CachedAsyncIterable = class extends CachedIterable {
		constructor(iterable) {
			super();
			if (Symbol.asyncIterator in Object(iterable)) this.iterator = iterable[Symbol.asyncIterator]();
			else if (Symbol.iterator in Object(iterable)) this.iterator = iterable[Symbol.iterator]();
			else throw new TypeError("Argument must implement the iteration protocol.");
		}
		[Symbol.asyncIterator]() {
			const cached = this;
			let cur = 0;
			return { async next() {
				if (cached.length <= cur) cached.push(cached.iterator.next());
				return cached[cur++];
			} };
		}
		async touchNext(count = 1) {
			let idx = 0;
			while (idx++ < count) {
				const last = this[this.length - 1];
				if (last && (await last).done) break;
				this.push(this.iterator.next());
			}
			return this[this.length - 1];
		}
	};
	Localization = class {
		constructor(resourceIds = [], generateBundles) {
			this.resourceIds = resourceIds;
			this.generateBundles = generateBundles;
			this.onChange(true);
		}
		addResourceIds(resourceIds, eager = false) {
			this.resourceIds.push(...resourceIds);
			this.onChange(eager);
			return this.resourceIds.length;
		}
		removeResourceIds(resourceIds) {
			this.resourceIds = this.resourceIds.filter((r) => !resourceIds.includes(r));
			this.onChange();
			return this.resourceIds.length;
		}
		async formatWithFallback(keys, method) {
			const translations = [];
			let hasAtLeastOneBundle = false;
			for await (const bundle of this.bundles) {
				hasAtLeastOneBundle = true;
				const missingIds = keysFromBundle(method, bundle, keys, translations);
				if (missingIds.size === 0) break;
				if (typeof console !== "undefined") {
					const locale = bundle.locales[0];
					const ids = Array.from(missingIds).join(", ");
					console.warn(`[fluent] Missing translations in ${locale}: ${ids}`);
				}
			}
			if (!hasAtLeastOneBundle && typeof console !== "undefined") console.warn(`[fluent] Request for keys failed because no resource bundles got generated.
  keys: ${JSON.stringify(keys)}.
  resourceIds: ${JSON.stringify(this.resourceIds)}.`);
			return translations;
		}
		formatMessages(keys) {
			return this.formatWithFallback(keys, messageFromBundle);
		}
		formatValues(keys) {
			return this.formatWithFallback(keys, valueFromBundle);
		}
		async formatValue(id, args) {
			const [val] = await this.formatValues([{
				id,
				args
			}]);
			return val;
		}
		handleEvent() {
			this.onChange();
		}
		onChange(eager = false) {
			this.bundles = CachedAsyncIterable.from(this.generateBundles(this.resourceIds));
			if (eager) this.bundles.touchNext(2);
		}
	};
	L10NID_ATTR_NAME = "data-l10n-id";
	L10NARGS_ATTR_NAME = "data-l10n-args";
	L10N_ELEMENT_QUERY = `[${L10NID_ATTR_NAME}]`;
	DOMLocalization = class extends Localization {
		constructor(resourceIds, generateBundles) {
			super(resourceIds, generateBundles);
			this.roots = /* @__PURE__ */ new Set();
			this.pendingrAF = null;
			this.pendingElements = /* @__PURE__ */ new Set();
			this.windowElement = null;
			this.mutationObserver = null;
			this.observerConfig = {
				attributes: true,
				characterData: false,
				childList: true,
				subtree: true,
				attributeFilter: [L10NID_ATTR_NAME, L10NARGS_ATTR_NAME]
			};
		}
		onChange(eager = false) {
			super.onChange(eager);
			if (this.roots) this.translateRoots();
		}
		setAttributes(element, id, args) {
			element.setAttribute(L10NID_ATTR_NAME, id);
			if (args) element.setAttribute(L10NARGS_ATTR_NAME, JSON.stringify(args));
			else element.removeAttribute(L10NARGS_ATTR_NAME);
			return element;
		}
		getAttributes(element) {
			return {
				id: element.getAttribute(L10NID_ATTR_NAME),
				args: JSON.parse(element.getAttribute(L10NARGS_ATTR_NAME) || null)
			};
		}
		connectRoot(newRoot) {
			for (const root of this.roots) if (root === newRoot || root.contains(newRoot) || newRoot.contains(root)) throw new Error("Cannot add a root that overlaps with existing root.");
			if (this.windowElement) {
				if (this.windowElement !== newRoot.ownerDocument.defaultView) throw new Error(`Cannot connect a root:
          DOMLocalization already has a root from a different window.`);
			} else {
				this.windowElement = newRoot.ownerDocument.defaultView;
				this.mutationObserver = new this.windowElement.MutationObserver((mutations) => this.translateMutations(mutations));
			}
			this.roots.add(newRoot);
			this.mutationObserver.observe(newRoot, this.observerConfig);
		}
		disconnectRoot(root) {
			this.roots.delete(root);
			this.pauseObserving();
			if (this.roots.size === 0) {
				this.mutationObserver = null;
				if (this.windowElement && this.pendingrAF) this.windowElement.cancelAnimationFrame(this.pendingrAF);
				this.windowElement = null;
				this.pendingrAF = null;
				this.pendingElements.clear();
				return true;
			}
			this.resumeObserving();
			return false;
		}
		translateRoots() {
			const roots = Array.from(this.roots);
			return Promise.all(roots.map((root) => this.translateFragment(root)));
		}
		pauseObserving() {
			if (!this.mutationObserver) return;
			this.translateMutations(this.mutationObserver.takeRecords());
			this.mutationObserver.disconnect();
		}
		resumeObserving() {
			if (!this.mutationObserver) return;
			for (const root of this.roots) this.mutationObserver.observe(root, this.observerConfig);
		}
		translateMutations(mutations) {
			for (const mutation of mutations) switch (mutation.type) {
				case "attributes":
					if (mutation.target.hasAttribute("data-l10n-id")) this.pendingElements.add(mutation.target);
					break;
				case "childList": for (const addedNode of mutation.addedNodes) if (addedNode.nodeType === addedNode.ELEMENT_NODE) {
					if (addedNode.childElementCount) for (const element of this.getTranslatables(addedNode)) this.pendingElements.add(element);
					else if (addedNode.hasAttribute(L10NID_ATTR_NAME)) this.pendingElements.add(addedNode);
				}
			}
			if (this.pendingElements.size > 0) {
				if (this.pendingrAF === null) this.pendingrAF = this.windowElement.requestAnimationFrame(() => {
					this.translateElements(Array.from(this.pendingElements));
					this.pendingElements.clear();
					this.pendingrAF = null;
				});
			}
		}
		translateFragment(frag) {
			return this.translateElements(this.getTranslatables(frag));
		}
		async translateElements(elements) {
			if (!elements.length) return;
			const keys = elements.map(this.getKeysForElement);
			const translations = await this.formatMessages(keys);
			return this.applyTranslations(elements, translations);
		}
		applyTranslations(elements, translations) {
			this.pauseObserving();
			for (let i = 0; i < elements.length; i++) if (translations[i] !== void 0) translateElement(elements[i], translations[i]);
			this.resumeObserving();
		}
		getTranslatables(element) {
			const nodes = Array.from(element.querySelectorAll(L10N_ELEMENT_QUERY));
			if (typeof element.hasAttribute === "function" && element.hasAttribute(L10NID_ATTR_NAME)) nodes.push(element);
			return nodes;
		}
		getKeysForElement(element) {
			return {
				id: element.getAttribute(L10NID_ATTR_NAME),
				args: JSON.parse(element.getAttribute(L10NARGS_ATTR_NAME) || null)
			};
		}
	};
	L10n = class L10n {
		#dir;
		#elements;
		#lang;
		#l10n;
		constructor({ lang, isRTL }, l10n = null) {
			this.#lang = L10n.#fixupLangCode(lang);
			this.#l10n = l10n;
			this.#dir = isRTL ?? L10n.#isRTL(this.#lang) ? "rtl" : "ltr";
		}
		_setL10n(l10n) {
			this.#l10n = l10n;
		}
		getLanguage() {
			return this.#lang;
		}
		getDirection() {
			return this.#dir;
		}
		async get(ids, args = null, fallback) {
			if (Array.isArray(ids)) {
				ids = ids.map((id) => ({ id }));
				return (await this.#l10n.formatMessages(ids)).map((message) => message.value);
			}
			return (await this.#l10n.formatMessages([{
				id: ids,
				args
			}]))[0]?.value || fallback;
		}
		async translate(element) {
			(this.#elements ||= /* @__PURE__ */ new Set()).add(element);
			try {
				this.#l10n.connectRoot(element);
				await this.#l10n.translateRoots();
			} catch {}
		}
		async translateOnce(element) {
			try {
				await this.#l10n.translateElements([element]);
			} catch (ex) {
				console.error("translateOnce:", ex);
			}
		}
		async destroy() {
			if (this.#elements) {
				for (const element of this.#elements) this.#l10n.disconnectRoot(element);
				this.#elements.clear();
				this.#elements = null;
			}
			this.#l10n.pauseObserving();
		}
		pause() {
			this.#l10n.pauseObserving();
		}
		resume() {
			this.#l10n.resumeObserving();
		}
		static #fixupLangCode(langCode) {
			langCode = langCode?.toLowerCase() || "en-us";
			return {
				en: "en-us",
				es: "es-es",
				fy: "fy-nl",
				ga: "ga-ie",
				gu: "gu-in",
				hi: "hi-in",
				hy: "hy-am",
				nb: "nb-no",
				ne: "ne-np",
				nn: "nn-no",
				pa: "pa-in",
				pt: "pt-pt",
				sv: "sv-se",
				zh: "zh-cn"
			}[langCode] || langCode;
		}
		static #isRTL(lang) {
			const shortCode = lang.split("-", 1)[0];
			return [
				"ar",
				"he",
				"fa",
				"ps",
				"ur"
			].includes(shortCode);
		}
	};
	genericl10n_GenericL10n = class genericl10n_GenericL10n extends L10n {
		constructor(lang) {
			super({ lang });
			const generateBundles = !lang ? genericl10n_GenericL10n.#generateBundlesFallback.bind(genericl10n_GenericL10n, this.getLanguage()) : genericl10n_GenericL10n.#generateBundles.bind(genericl10n_GenericL10n, "en-us", this.getLanguage());
			this._setL10n(new DOMLocalization([], generateBundles));
		}
		static async *#generateBundles(defaultLang, baseLang) {
			const { baseURL, paths } = await this.#getPaths();
			const langs = [baseLang];
			if (defaultLang !== baseLang) {
				const shortLang = baseLang.split("-", 1)[0];
				if (shortLang !== baseLang) langs.push(shortLang);
				langs.push(defaultLang);
			}
			for (const lang of langs) {
				const bundle = await this.#createBundle(lang, baseURL, paths);
				if (bundle) yield bundle;
				else if (lang === "en-us") yield this.#createBundleFallback(lang);
			}
		}
		static async #createBundle(lang, baseURL, paths) {
			const path = paths[lang];
			if (!path) return null;
			const url = new URL(path, baseURL);
			return createBundle(lang, await fetchData(url, "text"));
		}
		static async #getPaths() {
			try {
				const { href } = document.querySelector(`link[type="application/l10n"]`);
				const paths = await fetchData(href, "json");
				return {
					baseURL: href.replace(/[^/]*$/, "") || "./",
					paths
				};
			} catch {}
			return {
				baseURL: "./",
				paths: Object.create(null)
			};
		}
		static async *#generateBundlesFallback(lang) {
			yield this.#createBundleFallback(lang);
		}
		static async #createBundleFallback(lang) {
			return createBundle(lang, "pdfjs-previous-button =\n    .title = Previous Page\npdfjs-previous-button-label = Previous\npdfjs-next-button =\n    .title = Next Page\npdfjs-next-button-label = Next\npdfjs-page-input =\n    .title = Page\npdfjs-of-pages = of { $pagesCount }\npdfjs-page-of-pages = ({ $pageNumber } of { $pagesCount })\npdfjs-zoom-out-button =\n    .title = Zoom Out\npdfjs-zoom-out-button-label = Zoom Out\npdfjs-zoom-in-button =\n    .title = Zoom In\npdfjs-zoom-in-button-label = Zoom In\npdfjs-zoom-select =\n    .title = Zoom\npdfjs-presentation-mode-button =\n    .title = Switch to Presentation Mode\npdfjs-presentation-mode-button-label = Presentation Mode\npdfjs-open-file-button =\n    .title = Open File\npdfjs-open-file-button-label = Open\npdfjs-print-button =\n    .title = Print\npdfjs-print-button-label = Print\npdfjs-save-button =\n    .title = Save\npdfjs-save-button-label = Save\npdfjs-download-button =\n    .title = Download\npdfjs-download-button-label = Download\npdfjs-bookmark-button =\n    .title = Current Page (View URL from Current Page)\npdfjs-bookmark-button-label = Current Page\npdfjs-tools-button =\n    .title = Tools\npdfjs-tools-button-label = Tools\npdfjs-first-page-button =\n    .title = Go to First Page\npdfjs-first-page-button-label = Go to First Page\npdfjs-last-page-button =\n    .title = Go to Last Page\npdfjs-last-page-button-label = Go to Last Page\npdfjs-page-rotate-cw-button =\n    .title = Rotate Clockwise\npdfjs-page-rotate-cw-button-label = Rotate Clockwise\npdfjs-page-rotate-ccw-button =\n    .title = Rotate Counterclockwise\npdfjs-page-rotate-ccw-button-label = Rotate Counterclockwise\npdfjs-cursor-text-select-tool-button =\n    .title = Enable Text Selection Tool\npdfjs-cursor-text-select-tool-button-label = Text Selection Tool\npdfjs-cursor-hand-tool-button =\n    .title = Enable Hand Tool\npdfjs-cursor-hand-tool-button-label = Hand Tool\npdfjs-scroll-page-button =\n    .title = Use Page Scrolling\npdfjs-scroll-page-button-label = Page Scrolling\npdfjs-scroll-vertical-button =\n    .title = Use Vertical Scrolling\npdfjs-scroll-vertical-button-label = Vertical Scrolling\npdfjs-scroll-horizontal-button =\n    .title = Use Horizontal Scrolling\npdfjs-scroll-horizontal-button-label = Horizontal Scrolling\npdfjs-scroll-wrapped-button =\n    .title = Use Wrapped Scrolling\npdfjs-scroll-wrapped-button-label = Wrapped Scrolling\npdfjs-spread-none-button =\n    .title = Do not join page spreads\npdfjs-spread-none-button-label = No Spreads\npdfjs-spread-odd-button =\n    .title = Join page spreads starting with odd-numbered pages\npdfjs-spread-odd-button-label = Odd Spreads\npdfjs-spread-even-button =\n    .title = Join page spreads starting with even-numbered pages\npdfjs-spread-even-button-label = Even Spreads\npdfjs-document-properties-button =\n    .title = Document Properties…\npdfjs-document-properties-button-label = Document Properties…\npdfjs-document-properties-file-name = File name:\npdfjs-document-properties-file-size = File size:\npdfjs-document-properties-size-kb = { NUMBER($kb, maximumSignificantDigits: 3) } KB ({ $b } bytes)\npdfjs-document-properties-size-mb = { NUMBER($mb, maximumSignificantDigits: 3) } MB ({ $b } bytes)\npdfjs-document-properties-title = Title:\npdfjs-document-properties-author = Author:\npdfjs-document-properties-subject = Subject:\npdfjs-document-properties-keywords = Keywords:\npdfjs-document-properties-creation-date = Creation Date:\npdfjs-document-properties-modification-date = Modification Date:\npdfjs-document-properties-date-time-string = { DATETIME($dateObj, dateStyle: \"short\", timeStyle: \"medium\") }\npdfjs-document-properties-creator = Creator:\npdfjs-document-properties-producer = PDF Producer:\npdfjs-document-properties-version = PDF Version:\npdfjs-document-properties-page-count = Page Count:\npdfjs-document-properties-page-size = Page Size:\npdfjs-document-properties-page-size-unit-inches = in\npdfjs-document-properties-page-size-unit-millimeters = mm\npdfjs-document-properties-page-size-orientation-portrait = portrait\npdfjs-document-properties-page-size-orientation-landscape = landscape\npdfjs-document-properties-page-size-name-a-three = A3\npdfjs-document-properties-page-size-name-a-four = A4\npdfjs-document-properties-page-size-name-letter = Letter\npdfjs-document-properties-page-size-name-legal = Legal\npdfjs-document-properties-page-size-dimension-string = { $width } × { $height } { $unit } ({ $orientation })\npdfjs-document-properties-page-size-dimension-name-string = { $width } × { $height } { $unit } ({ $name }, { $orientation })\npdfjs-document-properties-linearized = Fast Web View:\npdfjs-document-properties-linearized-yes = Yes\npdfjs-document-properties-linearized-no = No\npdfjs-document-properties-close-button = Close\npdfjs-print-progress-message = Preparing document for printing…\npdfjs-print-progress-percent = { $progress }%\npdfjs-print-progress-close-button = Cancel\npdfjs-printing-not-supported = Warning: Printing is not fully supported by this browser.\npdfjs-printing-not-ready = Warning: The PDF is not fully loaded for printing.\npdfjs-toggle-sidebar-button =\n    .title = Toggle Sidebar\npdfjs-toggle-sidebar-notification-button =\n    .title = Toggle Sidebar (document contains outline/attachments/layers)\npdfjs-toggle-sidebar-button-label = Toggle Sidebar\npdfjs-document-outline-button =\n    .title = Show Document Outline (double-click to expand/collapse all items)\npdfjs-document-outline-button-label = Document Outline\npdfjs-attachments-button =\n    .title = Show Attachments\npdfjs-attachments-button-label = Attachments\npdfjs-layers-button =\n    .title = Show Layers (double-click to reset all layers to the default state)\npdfjs-layers-button-label = Layers\npdfjs-thumbs-button =\n    .title = Show Thumbnails\npdfjs-thumbs-button-label = Thumbnails\npdfjs-current-outline-item-button =\n    .title = Find Current Outline Item\npdfjs-current-outline-item-button-label = Current Outline Item\npdfjs-findbar-button =\n    .title = Find in Document\npdfjs-findbar-button-label = Find\npdfjs-additional-layers = Additional Layers\npdfjs-thumb-page-title =\n    .title = Page { $page }\npdfjs-thumb-page-canvas =\n    .aria-label = Thumbnail of Page { $page }\npdfjs-find-input =\n    .title = Find\n    .placeholder = Find in document…\npdfjs-find-previous-button =\n    .title = Find the previous occurrence of the phrase\npdfjs-find-previous-button-label = Previous\npdfjs-find-next-button =\n    .title = Find the next occurrence of the phrase\npdfjs-find-next-button-label = Next\npdfjs-find-highlight-checkbox = Highlight All\npdfjs-find-match-case-checkbox-label = Match Case\npdfjs-find-match-diacritics-checkbox-label = Match Diacritics\npdfjs-find-entire-word-checkbox-label = Whole Words\npdfjs-find-reached-top = Reached top of document, continued from bottom\npdfjs-find-reached-bottom = Reached end of document, continued from top\npdfjs-find-match-count =\n    { $total ->\n        [one] { $current } of { $total } match\n       *[other] { $current } of { $total } matches\n    }\npdfjs-find-match-count-limit =\n    { $limit ->\n        [one] More than { $limit } match\n       *[other] More than { $limit } matches\n    }\npdfjs-find-not-found = Phrase not found\npdfjs-page-scale-width = Page Width\npdfjs-page-scale-fit = Page Fit\npdfjs-page-scale-auto = Automatic Zoom\npdfjs-page-scale-actual = Actual Size\npdfjs-page-scale-percent = { $scale }%\npdfjs-page-landmark =\n    .aria-label = Page { $page }\npdfjs-loading-error = An error occurred while loading the PDF.\npdfjs-invalid-file-error = Invalid or corrupted PDF file.\npdfjs-missing-file-error = Missing PDF file.\npdfjs-unexpected-response-error = Unexpected server response.\npdfjs-rendering-error = An error occurred while rendering the page.\npdfjs-annotation-date-time-string = { DATETIME($dateObj, dateStyle: \"short\", timeStyle: \"medium\") }\npdfjs-text-annotation-type =\n    .alt = [{ $type } Annotation]\npdfjs-password-label = Enter the password to open this PDF file.\npdfjs-password-invalid = Invalid password. Please try again.\npdfjs-password-ok-button = OK\npdfjs-password-cancel-button = Cancel\npdfjs-web-fonts-disabled = Web fonts are disabled: unable to use embedded PDF fonts.\npdfjs-editor-free-text-button =\n    .title = Text\npdfjs-editor-free-text-button-label = Text\npdfjs-editor-ink-button =\n    .title = Draw\npdfjs-editor-ink-button-label = Draw\npdfjs-editor-stamp-button =\n    .title = Add or edit images\npdfjs-editor-stamp-button-label = Add or edit images\npdfjs-editor-highlight-button =\n    .title = Highlight\npdfjs-editor-highlight-button-label = Highlight\npdfjs-highlight-floating-button1 =\n    .title = Highlight\n    .aria-label = Highlight\npdfjs-highlight-floating-button-label = Highlight\npdfjs-editor-remove-ink-button =\n    .title = Remove drawing\npdfjs-editor-remove-freetext-button =\n    .title = Remove text\npdfjs-editor-remove-stamp-button =\n    .title = Remove image\npdfjs-editor-remove-highlight-button =\n    .title = Remove highlight\npdfjs-editor-free-text-color-input = Color\npdfjs-editor-free-text-size-input = Size\npdfjs-editor-ink-color-input = Color\npdfjs-editor-ink-thickness-input = Thickness\npdfjs-editor-ink-opacity-input = Opacity\npdfjs-editor-stamp-add-image-button =\n    .title = Add image\npdfjs-editor-stamp-add-image-button-label = Add image\npdfjs-editor-free-highlight-thickness-input = Thickness\npdfjs-editor-free-highlight-thickness-title =\n    .title = Change thickness when highlighting items other than text\npdfjs-free-text2 =\n    .aria-label = Text Editor\n    .default-content = Start typing…\npdfjs-ink =\n    .aria-label = Draw Editor\npdfjs-ink-canvas =\n    .aria-label = User-created image\npdfjs-editor-alt-text-button =\n    .aria-label = Alt text\npdfjs-editor-alt-text-button-label = Alt text\npdfjs-editor-alt-text-edit-button =\n    .aria-label = Edit alt text\npdfjs-editor-alt-text-dialog-label = Choose an option\npdfjs-editor-alt-text-dialog-description = Alt text (alternative text) helps when people can’t see the image or when it doesn’t load.\npdfjs-editor-alt-text-add-description-label = Add a description\npdfjs-editor-alt-text-add-description-description = Aim for 1-2 sentences that describe the subject, setting, or actions.\npdfjs-editor-alt-text-mark-decorative-label = Mark as decorative\npdfjs-editor-alt-text-mark-decorative-description = This is used for ornamental images, like borders or watermarks.\npdfjs-editor-alt-text-cancel-button = Cancel\npdfjs-editor-alt-text-save-button = Save\npdfjs-editor-alt-text-decorative-tooltip = Marked as decorative\npdfjs-editor-alt-text-textarea =\n    .placeholder = For example, “A young man sits down at a table to eat a meal”\npdfjs-editor-resizer-top-left =\n    .aria-label = Top left corner — resize\npdfjs-editor-resizer-top-middle =\n    .aria-label = Top middle — resize\npdfjs-editor-resizer-top-right =\n    .aria-label = Top right corner — resize\npdfjs-editor-resizer-middle-right =\n    .aria-label = Middle right — resize\npdfjs-editor-resizer-bottom-right =\n    .aria-label = Bottom right corner — resize\npdfjs-editor-resizer-bottom-middle =\n    .aria-label = Bottom middle — resize\npdfjs-editor-resizer-bottom-left =\n    .aria-label = Bottom left corner — resize\npdfjs-editor-resizer-middle-left =\n    .aria-label = Middle left — resize\npdfjs-editor-highlight-colorpicker-label = Highlight color\npdfjs-editor-colorpicker-button =\n    .title = Change color\npdfjs-editor-colorpicker-dropdown =\n    .aria-label = Color choices\npdfjs-editor-colorpicker-yellow =\n    .title = Yellow\npdfjs-editor-colorpicker-green =\n    .title = Green\npdfjs-editor-colorpicker-blue =\n    .title = Blue\npdfjs-editor-colorpicker-pink =\n    .title = Pink\npdfjs-editor-colorpicker-red =\n    .title = Red\npdfjs-editor-highlight-show-all-button-label = Show all\npdfjs-editor-highlight-show-all-button =\n    .title = Show all\npdfjs-editor-new-alt-text-dialog-edit-label = Edit alt text (image description)\npdfjs-editor-new-alt-text-dialog-add-label = Add alt text (image description)\npdfjs-editor-new-alt-text-textarea =\n    .placeholder = Write your description here…\npdfjs-editor-new-alt-text-description = Short description for people who can’t see the image or when the image doesn’t load.\npdfjs-editor-new-alt-text-disclaimer1 = This alt text was created automatically and may be inaccurate.\npdfjs-editor-new-alt-text-disclaimer-learn-more-url = Learn more\npdfjs-editor-new-alt-text-create-automatically-button-label = Create alt text automatically\npdfjs-editor-new-alt-text-not-now-button = Not now\npdfjs-editor-new-alt-text-error-title = Couldn’t create alt text automatically\npdfjs-editor-new-alt-text-error-description = Please write your own alt text or try again later.\npdfjs-editor-new-alt-text-error-close-button = Close\npdfjs-editor-new-alt-text-ai-model-downloading-progress = Downloading alt text AI model ({ $downloadedSize } of { $totalSize } MB)\n    .aria-valuetext = Downloading alt text AI model ({ $downloadedSize } of { $totalSize } MB)\npdfjs-editor-new-alt-text-added-button =\n    .aria-label = Alt text added\npdfjs-editor-new-alt-text-added-button-label = Alt text added\npdfjs-editor-new-alt-text-missing-button =\n    .aria-label = Missing alt text\npdfjs-editor-new-alt-text-missing-button-label = Missing alt text\npdfjs-editor-new-alt-text-to-review-button =\n    .aria-label = Review alt text\npdfjs-editor-new-alt-text-to-review-button-label = Review alt text\npdfjs-editor-new-alt-text-generated-alt-text-with-disclaimer = Created automatically: { $generatedAltText }\npdfjs-image-alt-text-settings-button =\n    .title = Image alt text settings\npdfjs-image-alt-text-settings-button-label = Image alt text settings\npdfjs-editor-alt-text-settings-dialog-label = Image alt text settings\npdfjs-editor-alt-text-settings-automatic-title = Automatic alt text\npdfjs-editor-alt-text-settings-create-model-button-label = Create alt text automatically\npdfjs-editor-alt-text-settings-create-model-description = Suggests descriptions to help people who can’t see the image or when the image doesn’t load.\npdfjs-editor-alt-text-settings-download-model-label = Alt text AI model ({ $totalSize } MB)\npdfjs-editor-alt-text-settings-ai-model-description = Runs locally on your device so your data stays private. Required for automatic alt text.\npdfjs-editor-alt-text-settings-delete-model-button = Delete\npdfjs-editor-alt-text-settings-download-model-button = Download\npdfjs-editor-alt-text-settings-downloading-model-button = Downloading…\npdfjs-editor-alt-text-settings-editor-title = Alt text editor\npdfjs-editor-alt-text-settings-show-dialog-button-label = Show alt text editor right away when adding an image\npdfjs-editor-alt-text-settings-show-dialog-description = Helps you make sure all your images have alt text.\npdfjs-editor-alt-text-settings-close-button = Close\npdfjs-editor-undo-bar-message-highlight = Highlight removed\npdfjs-editor-undo-bar-message-freetext = Text removed\npdfjs-editor-undo-bar-message-ink = Drawing removed\npdfjs-editor-undo-bar-message-stamp = Image removed\npdfjs-editor-undo-bar-message-multiple =\n    { $count ->\n        [one] { $count } annotation removed\n       *[other] { $count } annotations removed\n    }\npdfjs-editor-undo-bar-undo-button =\n    .title = Undo\npdfjs-editor-undo-bar-undo-button-label = Undo\npdfjs-editor-undo-bar-close-button =\n    .title = Close\npdfjs-editor-undo-bar-close-button-label = Close");
		}
	};
	HASH_CHANGE_TIMEOUT = 1e3;
	POSITION_UPDATED_THRESHOLD = 50;
	UPDATE_VIEWAREA_TIMEOUT = 1e3;
	PDFHistory = class {
		#eventAbortController = null;
		constructor({ linkService, eventBus }) {
			this.linkService = linkService;
			this.eventBus = eventBus;
			this._initialized = false;
			this._fingerprint = "";
			this.reset();
			this.eventBus._on("pagesinit", () => {
				this._isPagesLoaded = false;
				this.eventBus._on("pagesloaded", (evt) => {
					this._isPagesLoaded = !!evt.pagesCount;
				}, { once: true });
			});
		}
		initialize({ fingerprint, resetHistory = false, updateUrl = false }) {
			if (!fingerprint || typeof fingerprint !== "string") {
				console.error("PDFHistory.initialize: The \"fingerprint\" must be a non-empty string.");
				return;
			}
			if (this._initialized) this.reset();
			const reInitialized = this._fingerprint !== "" && this._fingerprint !== fingerprint;
			this._fingerprint = fingerprint;
			this._updateUrl = updateUrl === true;
			this._initialized = true;
			this.#bindEvents();
			const state = window.history.state;
			this._popStateInProgress = false;
			this._blockHashChange = 0;
			this._currentHash = getCurrentHash();
			this._numPositionUpdates = 0;
			this._uid = this._maxUid = 0;
			this._destination = null;
			this._position = null;
			if (!this.#isValidState(state, true) || resetHistory) {
				const { hash, page, rotation } = this.#parseCurrentHash(true);
				if (!hash || reInitialized || resetHistory) {
					this.#pushOrReplaceState(null, true);
					return;
				}
				this.#pushOrReplaceState({
					hash,
					page,
					rotation
				}, true);
				return;
			}
			const destination = state.destination;
			this.#updateInternalState(destination, state.uid, true);
			if (destination.rotation !== void 0) this._initialRotation = destination.rotation;
			if (destination.dest) {
				this._initialBookmark = JSON.stringify(destination.dest);
				this._destination.page = null;
			} else if (destination.hash) this._initialBookmark = destination.hash;
			else if (destination.page) this._initialBookmark = `page=${destination.page}`;
		}
		reset() {
			if (this._initialized) {
				this.#pageHide();
				this._initialized = false;
				this.#unbindEvents();
			}
			if (this._updateViewareaTimeout) {
				clearTimeout(this._updateViewareaTimeout);
				this._updateViewareaTimeout = null;
			}
			this._initialBookmark = null;
			this._initialRotation = null;
		}
		push({ namedDest = null, explicitDest, pageNumber }) {
			if (!this._initialized) return;
			if (namedDest && typeof namedDest !== "string") {
				console.error(`PDFHistory.push: "${namedDest}" is not a valid namedDest parameter.`);
				return;
			} else if (!Array.isArray(explicitDest)) {
				console.error(`PDFHistory.push: "${explicitDest}" is not a valid explicitDest parameter.`);
				return;
			} else if (!this.#isValidPage(pageNumber)) {
				if (pageNumber !== null || this._destination) {
					console.error(`PDFHistory.push: "${pageNumber}" is not a valid pageNumber parameter.`);
					return;
				}
			}
			const hash = namedDest || JSON.stringify(explicitDest);
			if (!hash) return;
			let forceReplace = false;
			if (this._destination && (isDestHashesEqual(this._destination.hash, hash) || isDestArraysEqual(this._destination.dest, explicitDest))) {
				if (this._destination.page) return;
				forceReplace = true;
			}
			if (this._popStateInProgress && !forceReplace) return;
			this.#pushOrReplaceState({
				dest: explicitDest,
				hash,
				page: pageNumber,
				rotation: this.linkService.rotation
			}, forceReplace);
			if (!this._popStateInProgress) {
				this._popStateInProgress = true;
				Promise.resolve().then(() => {
					this._popStateInProgress = false;
				});
			}
		}
		pushPage(pageNumber) {
			if (!this._initialized) return;
			if (!this.#isValidPage(pageNumber)) {
				console.error(`PDFHistory.pushPage: "${pageNumber}" is not a valid page number.`);
				return;
			}
			if (this._destination?.page === pageNumber) return;
			if (this._popStateInProgress) return;
			this.#pushOrReplaceState({
				dest: null,
				hash: `page=${pageNumber}`,
				page: pageNumber,
				rotation: this.linkService.rotation
			});
			if (!this._popStateInProgress) {
				this._popStateInProgress = true;
				Promise.resolve().then(() => {
					this._popStateInProgress = false;
				});
			}
		}
		pushCurrentPosition() {
			if (!this._initialized || this._popStateInProgress) return;
			this.#tryPushCurrentPosition();
		}
		back() {
			if (!this._initialized || this._popStateInProgress) return;
			const state = window.history.state;
			if (this.#isValidState(state) && state.uid > 0) window.history.back();
		}
		forward() {
			if (!this._initialized || this._popStateInProgress) return;
			const state = window.history.state;
			if (this.#isValidState(state) && state.uid < this._maxUid) window.history.forward();
		}
		get popStateInProgress() {
			return this._initialized && (this._popStateInProgress || this._blockHashChange > 0);
		}
		get initialBookmark() {
			return this._initialized ? this._initialBookmark : null;
		}
		get initialRotation() {
			return this._initialized ? this._initialRotation : null;
		}
		#pushOrReplaceState(destination, forceReplace = false) {
			const shouldReplace = forceReplace || !this._destination;
			const newState = {
				fingerprint: this._fingerprint,
				uid: shouldReplace ? this._uid : this._uid + 1,
				destination
			};
			this.#updateInternalState(destination, newState.uid);
			let newUrl;
			if (this._updateUrl && destination?.hash) {
				const baseUrl = document.location.href.split("#", 1)[0];
				if (!baseUrl.startsWith("file://")) newUrl = `${baseUrl}#${destination.hash}`;
			}
			if (shouldReplace) window.history.replaceState(newState, "", newUrl);
			else window.history.pushState(newState, "", newUrl);
		}
		#tryPushCurrentPosition(temporary = false) {
			if (!this._position) return;
			let position = this._position;
			if (temporary) {
				position = Object.assign(Object.create(null), this._position);
				position.temporary = true;
			}
			if (!this._destination) {
				this.#pushOrReplaceState(position);
				return;
			}
			if (this._destination.temporary) {
				this.#pushOrReplaceState(position, true);
				return;
			}
			if (this._destination.hash === position.hash) return;
			if (!this._destination.page && this._numPositionUpdates <= POSITION_UPDATED_THRESHOLD) return;
			let forceReplace = false;
			if (this._destination.page >= position.first && this._destination.page <= position.page) {
				if (this._destination.dest !== void 0 || !this._destination.first) return;
				forceReplace = true;
			}
			this.#pushOrReplaceState(position, forceReplace);
		}
		#isValidPage(val) {
			return Number.isInteger(val) && val > 0 && val <= this.linkService.pagesCount;
		}
		#isValidState(state, checkReload = false) {
			if (!state) return false;
			if (state.fingerprint !== this._fingerprint) {
				if (checkReload) {
					if (typeof state.fingerprint !== "string" || state.fingerprint.length !== this._fingerprint.length) return false;
					const [perfEntry] = performance.getEntriesByType("navigation");
					if (perfEntry?.type !== "reload") return false;
				} else return false;
			}
			if (!Number.isInteger(state.uid) || state.uid < 0) return false;
			if (state.destination === null || typeof state.destination !== "object") return false;
			return true;
		}
		#updateInternalState(destination, uid, removeTemporary = false) {
			if (this._updateViewareaTimeout) {
				clearTimeout(this._updateViewareaTimeout);
				this._updateViewareaTimeout = null;
			}
			if (removeTemporary && destination?.temporary) delete destination.temporary;
			this._destination = destination;
			this._uid = uid;
			this._maxUid = Math.max(this._maxUid, uid);
			this._numPositionUpdates = 0;
		}
		#parseCurrentHash(checkNameddest = false) {
			const hash = unescape(getCurrentHash()).substring(1);
			const params = parseQueryString(hash);
			const nameddest = params.get("nameddest") || "";
			let page = params.get("page") | 0;
			if (!this.#isValidPage(page) || checkNameddest && nameddest.length > 0) page = null;
			return {
				hash,
				page,
				rotation: this.linkService.rotation
			};
		}
		#updateViewarea({ location }) {
			if (this._updateViewareaTimeout) {
				clearTimeout(this._updateViewareaTimeout);
				this._updateViewareaTimeout = null;
			}
			this._position = {
				hash: location.pdfOpenParams.substring(1),
				page: this.linkService.page,
				first: location.pageNumber,
				rotation: location.rotation
			};
			if (this._popStateInProgress) return;
			if (this._isPagesLoaded && this._destination && !this._destination.page) this._numPositionUpdates++;
			this._updateViewareaTimeout = setTimeout(() => {
				if (!this._popStateInProgress) this.#tryPushCurrentPosition(true);
				this._updateViewareaTimeout = null;
			}, UPDATE_VIEWAREA_TIMEOUT);
		}
		#popState({ state }) {
			const newHash = getCurrentHash(), hashChanged = this._currentHash !== newHash;
			this._currentHash = newHash;
			if (!state) {
				this._uid++;
				const { hash, page, rotation } = this.#parseCurrentHash();
				this.#pushOrReplaceState({
					hash,
					page,
					rotation
				}, true);
				return;
			}
			if (!this.#isValidState(state)) return;
			this._popStateInProgress = true;
			if (hashChanged) {
				this._blockHashChange++;
				waitOnEventOrTimeout({
					target: window,
					name: "hashchange",
					delay: HASH_CHANGE_TIMEOUT
				}).then(() => {
					this._blockHashChange--;
				});
			}
			const destination = state.destination;
			this.#updateInternalState(destination, state.uid, true);
			if (isValidRotation(destination.rotation)) this.linkService.rotation = destination.rotation;
			if (destination.dest) this.linkService.goToDestination(destination.dest);
			else if (destination.hash) this.linkService.setHash(destination.hash);
			else if (destination.page) this.linkService.page = destination.page;
			Promise.resolve().then(() => {
				this._popStateInProgress = false;
			});
		}
		#pageHide() {
			if (!this._destination || this._destination.temporary) this.#tryPushCurrentPosition();
		}
		#bindEvents() {
			if (this.#eventAbortController) return;
			this.#eventAbortController = new AbortController();
			const { signal } = this.#eventAbortController;
			this.eventBus._on("updateviewarea", this.#updateViewarea.bind(this), { signal });
			window.addEventListener("popstate", this.#popState.bind(this), { signal });
			window.addEventListener("pagehide", this.#pageHide.bind(this), { signal });
		}
		#unbindEvents() {
			this.#eventAbortController?.abort();
			this.#eventAbortController = null;
		}
	};
	AnnotationEditorLayerBuilder = class {
		#annotationLayer = null;
		#drawLayer = null;
		#onAppend = null;
		#structTreeLayer = null;
		#textLayer = null;
		#uiManager;
		constructor(options) {
			this.pdfPage = options.pdfPage;
			this.accessibilityManager = options.accessibilityManager;
			this.l10n = options.l10n;
			this.l10n ||= new genericl10n_GenericL10n();
			this.annotationEditorLayer = null;
			this.div = null;
			this._cancelled = false;
			this.#uiManager = options.uiManager;
			this.#annotationLayer = options.annotationLayer || null;
			this.#textLayer = options.textLayer || null;
			this.#drawLayer = options.drawLayer || null;
			this.#onAppend = options.onAppend || null;
			this.#structTreeLayer = options.structTreeLayer || null;
		}
		async render(viewport, intent = "display") {
			if (intent !== "display") return;
			if (this._cancelled) return;
			const clonedViewport = viewport.clone({ dontFlip: true });
			if (this.div) {
				this.annotationEditorLayer.update({ viewport: clonedViewport });
				this.show();
				return;
			}
			const div = this.div = document.createElement("div");
			div.className = "annotationEditorLayer";
			div.hidden = true;
			div.dir = this.#uiManager.direction;
			this.#onAppend?.(div);
			this.annotationEditorLayer = new AnnotationEditorLayer({
				uiManager: this.#uiManager,
				div,
				structTreeLayer: this.#structTreeLayer,
				accessibilityManager: this.accessibilityManager,
				pageIndex: this.pdfPage.pageNumber - 1,
				l10n: this.l10n,
				viewport: clonedViewport,
				annotationLayer: this.#annotationLayer,
				textLayer: this.#textLayer,
				drawLayer: this.#drawLayer
			});
			const parameters = {
				viewport: clonedViewport,
				div,
				annotations: null,
				intent
			};
			this.annotationEditorLayer.render(parameters);
			this.show();
		}
		cancel() {
			this._cancelled = true;
			if (!this.div) return;
			this.annotationEditorLayer.destroy();
		}
		hide() {
			if (!this.div) return;
			this.annotationEditorLayer.pause(true);
			this.div.hidden = true;
		}
		show() {
			if (!this.div || this.annotationEditorLayer.isInvisible) return;
			this.div.hidden = false;
			this.annotationEditorLayer.pause(false);
		}
	};
	{
		compatParams = /* @__PURE__ */ new Map();
		const userAgent = navigator.userAgent || "";
		const platform = navigator.platform || "";
		const maxTouchPoints = navigator.maxTouchPoints || 1;
		const isAndroid = /Android/.test(userAgent);
		const isIOS = /\b(iPad|iPhone|iPod)(?=;)/.test(userAgent) || platform === "MacIntel" && maxTouchPoints > 1;
		(function() {
			if (isIOS || isAndroid) compatParams.set("maxCanvasPixels", 5242880);
		})();
		(function() {
			if (isAndroid) compatParams.set("useSystemFonts", false);
		})();
	}
	OptionKind = {
		BROWSER: 1,
		VIEWER: 2,
		API: 4,
		WORKER: 8,
		EVENT_DISPATCH: 16,
		PREFERENCE: 128
	};
	Type = {
		BOOLEAN: 1,
		NUMBER: 2,
		OBJECT: 4,
		STRING: 8,
		UNDEFINED: 16
	};
	defaultOptions = {
		allowedGlobalEvents: {
			value: null,
			kind: OptionKind.BROWSER
		},
		canvasMaxAreaInBytes: {
			value: -1,
			kind: OptionKind.BROWSER + OptionKind.API
		},
		isInAutomation: {
			value: false,
			kind: OptionKind.BROWSER
		},
		localeProperties: {
			value: { lang: navigator.language || "en-US" },
			kind: OptionKind.BROWSER
		},
		nimbusDataStr: {
			value: "",
			kind: OptionKind.BROWSER
		},
		supportsCaretBrowsingMode: {
			value: false,
			kind: OptionKind.BROWSER
		},
		supportsDocumentFonts: {
			value: true,
			kind: OptionKind.BROWSER
		},
		supportsIntegratedFind: {
			value: false,
			kind: OptionKind.BROWSER
		},
		supportsMouseWheelZoomCtrlKey: {
			value: true,
			kind: OptionKind.BROWSER
		},
		supportsMouseWheelZoomMetaKey: {
			value: true,
			kind: OptionKind.BROWSER
		},
		supportsPinchToZoom: {
			value: true,
			kind: OptionKind.BROWSER
		},
		toolbarDensity: {
			value: 0,
			kind: OptionKind.BROWSER + OptionKind.EVENT_DISPATCH
		},
		altTextLearnMoreUrl: {
			value: "",
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		annotationEditorMode: {
			value: 0,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		annotationMode: {
			value: 2,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		cursorToolOnLoad: {
			value: 0,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		debuggerSrc: {
			value: "./debugger.mjs",
			kind: OptionKind.VIEWER
		},
		defaultZoomDelay: {
			value: 400,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		defaultZoomValue: {
			value: "",
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		disableHistory: {
			value: false,
			kind: OptionKind.VIEWER
		},
		disablePageLabels: {
			value: false,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		enableAltText: {
			value: false,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		enableAltTextModelDownload: {
			value: true,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE + OptionKind.EVENT_DISPATCH
		},
		enableGuessAltText: {
			value: true,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE + OptionKind.EVENT_DISPATCH
		},
		enableHighlightFloatingButton: {
			value: false,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		enableNewAltTextWhenAddingImage: {
			value: true,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		enablePermissions: {
			value: false,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		enablePrintAutoRotate: {
			value: true,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		enableScripting: {
			value: true,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		enableUpdatedAddImage: {
			value: false,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		externalLinkRel: {
			value: "noopener noreferrer nofollow",
			kind: OptionKind.VIEWER
		},
		externalLinkTarget: {
			value: 0,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		highlightEditorColors: {
			value: "yellow=#FFFF98,green=#53FFBC,blue=#80EBFF,pink=#FFCBE6,red=#FF4F5F",
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		historyUpdateUrl: {
			value: false,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		ignoreDestinationZoom: {
			value: false,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		imageResourcesPath: {
			value: "./images/",
			kind: OptionKind.VIEWER
		},
		maxCanvasPixels: {
			value: 2 ** 25,
			kind: OptionKind.VIEWER
		},
		forcePageColors: {
			value: false,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		pageColorsBackground: {
			value: "Canvas",
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		pageColorsForeground: {
			value: "CanvasText",
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		pdfBugEnabled: {
			value: false,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		printResolution: {
			value: 150,
			kind: OptionKind.VIEWER
		},
		sidebarViewOnLoad: {
			value: -1,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		scrollModeOnLoad: {
			value: -1,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		spreadModeOnLoad: {
			value: -1,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		textLayerMode: {
			value: 1,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		viewOnLoad: {
			value: 0,
			kind: OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		cMapPacked: {
			value: true,
			kind: OptionKind.API
		},
		cMapUrl: {
			value: "../web/cmaps/",
			kind: OptionKind.API
		},
		disableAutoFetch: {
			value: false,
			kind: OptionKind.API + OptionKind.PREFERENCE
		},
		disableFontFace: {
			value: false,
			kind: OptionKind.API + OptionKind.PREFERENCE
		},
		disableRange: {
			value: false,
			kind: OptionKind.API + OptionKind.PREFERENCE
		},
		disableStream: {
			value: false,
			kind: OptionKind.API + OptionKind.PREFERENCE
		},
		docBaseUrl: {
			value: "",
			kind: OptionKind.API
		},
		enableHWA: {
			value: true,
			kind: OptionKind.API + OptionKind.VIEWER + OptionKind.PREFERENCE
		},
		enableXfa: {
			value: true,
			kind: OptionKind.API + OptionKind.PREFERENCE
		},
		fontExtraProperties: {
			value: false,
			kind: OptionKind.API
		},
		isEvalSupported: {
			value: true,
			kind: OptionKind.API
		},
		isOffscreenCanvasSupported: {
			value: true,
			kind: OptionKind.API
		},
		maxImageSize: {
			value: -1,
			kind: OptionKind.API
		},
		pdfBug: {
			value: false,
			kind: OptionKind.API
		},
		standardFontDataUrl: {
			value: "../web/standard_fonts/",
			kind: OptionKind.API
		},
		useSystemFonts: {
			value: void 0,
			kind: OptionKind.API,
			type: Type.BOOLEAN + Type.UNDEFINED
		},
		verbosity: {
			value: 1,
			kind: OptionKind.API
		},
		workerPort: {
			value: null,
			kind: OptionKind.WORKER
		},
		workerSrc: {
			value: "../build/pdf.worker.mjs",
			kind: OptionKind.WORKER
		}
	};
	defaultOptions.defaultUrl = {
		value: "compressed.tracemonkey-pldi-09.pdf",
		kind: OptionKind.VIEWER
	};
	defaultOptions.sandboxBundleSrc = {
		value: "../build/pdf.sandbox.mjs",
		kind: OptionKind.VIEWER
	};
	defaultOptions.viewerCssTheme = {
		value: 0,
		kind: OptionKind.VIEWER + OptionKind.PREFERENCE
	};
	defaultOptions.enableFakeMLManager = {
		value: true,
		kind: OptionKind.VIEWER
	};
	defaultOptions.disablePreferences = {
		value: false,
		kind: OptionKind.VIEWER
	};
	AppOptions = class {
		static eventBus;
		static #opts = /* @__PURE__ */ new Map();
		static {
			for (const name in defaultOptions) this.#opts.set(name, defaultOptions[name].value);
			for (const [name, value] of compatParams) this.#opts.set(name, value);
			this._hasInvokedSet = false;
			this._checkDisablePreferences = () => {
				if (this.get("disablePreferences")) return true;
				if (this._hasInvokedSet) console.warn("The Preferences may override manually set AppOptions; please use the \"disablePreferences\"-option to prevent that.");
				return false;
			};
		}
		static get(name) {
			return this.#opts.get(name);
		}
		static getAll(kind = null, defaultOnly = false) {
			const options = Object.create(null);
			for (const name in defaultOptions) {
				const defaultOpt = defaultOptions[name];
				if (kind && !(kind & defaultOpt.kind)) continue;
				options[name] = !defaultOnly ? this.#opts.get(name) : defaultOpt.value;
			}
			return options;
		}
		static set(name, value) {
			this.setAll({ [name]: value });
		}
		static setAll(options, prefs = false) {
			this._hasInvokedSet ||= true;
			let events;
			for (const name in options) {
				const defaultOpt = defaultOptions[name], userOpt = options[name];
				if (!defaultOpt || !(typeof userOpt === typeof defaultOpt.value || Type[(typeof userOpt).toUpperCase()] & defaultOpt.type)) continue;
				const { kind } = defaultOpt;
				if (prefs && !(kind & OptionKind.BROWSER || kind & OptionKind.PREFERENCE)) continue;
				if (this.eventBus && kind & OptionKind.EVENT_DISPATCH) (events ||= /* @__PURE__ */ new Map()).set(name, userOpt);
				this.#opts.set(name, userOpt);
			}
			if (events) for (const [name, value] of events) this.eventBus.dispatch(name.toLowerCase(), {
				source: this,
				value
			});
		}
	};
	DrawLayerBuilder = class {
		#drawLayer = null;
		constructor(options) {
			this.pageIndex = options.pageIndex;
		}
		async render(intent = "display") {
			if (intent !== "display" || this.#drawLayer || this._cancelled) return;
			this.#drawLayer = new DrawLayer({ pageIndex: this.pageIndex });
		}
		cancel() {
			this._cancelled = true;
			if (!this.#drawLayer) return;
			this.#drawLayer.destroy();
			this.#drawLayer = null;
		}
		setParent(parent) {
			this.#drawLayer?.setParent(parent);
		}
		getDrawLayer() {
			return this.#drawLayer;
		}
	};
	PDF_ROLE_TO_HTML_ROLE = {
		Document: null,
		DocumentFragment: null,
		Part: "group",
		Sect: "group",
		Div: "group",
		Aside: "note",
		NonStruct: "none",
		P: null,
		H: "heading",
		Title: null,
		FENote: "note",
		Sub: "group",
		Lbl: null,
		Span: null,
		Em: null,
		Strong: null,
		Link: "link",
		Annot: "note",
		Form: "form",
		Ruby: null,
		RB: null,
		RT: null,
		RP: null,
		Warichu: null,
		WT: null,
		WP: null,
		L: "list",
		LI: "listitem",
		LBody: null,
		Table: "table",
		TR: "row",
		TH: "columnheader",
		TD: "cell",
		THead: "columnheader",
		TBody: null,
		TFoot: null,
		Caption: null,
		Figure: "figure",
		Formula: null,
		Artifact: null
	};
	HEADING_PATTERN = /^H(\d+)$/;
	StructTreeLayerBuilder = class {
		#promise;
		#treeDom = null;
		#treePromise;
		#elementAttributes = /* @__PURE__ */ new Map();
		#rawDims;
		#elementsToAddToTextLayer = null;
		constructor(pdfPage, rawDims) {
			this.#promise = pdfPage.getStructTree();
			this.#rawDims = rawDims;
		}
		async render() {
			if (this.#treePromise) return this.#treePromise;
			const { promise, resolve, reject } = Promise.withResolvers();
			this.#treePromise = promise;
			try {
				this.#treeDom = this.#walk(await this.#promise);
			} catch (ex) {
				reject(ex);
			}
			this.#promise = null;
			this.#treeDom?.classList.add("structTree");
			resolve(this.#treeDom);
			return promise;
		}
		async getAriaAttributes(annotationId) {
			try {
				await this.render();
				return this.#elementAttributes.get(annotationId);
			} catch {}
			return null;
		}
		hide() {
			if (this.#treeDom && !this.#treeDom.hidden) this.#treeDom.hidden = true;
		}
		show() {
			if (this.#treeDom?.hidden) this.#treeDom.hidden = false;
		}
		#setAttributes(structElement, htmlElement) {
			const { alt, id, lang } = structElement;
			if (alt !== void 0) {
				let added = false;
				const label = removeNullCharacters(alt);
				for (const child of structElement.children) if (child.type === "annotation") {
					let attrs = this.#elementAttributes.get(child.id);
					if (!attrs) {
						attrs = /* @__PURE__ */ new Map();
						this.#elementAttributes.set(child.id, attrs);
					}
					attrs.set("aria-label", label);
					added = true;
				}
				if (!added) htmlElement.setAttribute("aria-label", label);
			}
			if (id !== void 0) htmlElement.setAttribute("aria-owns", id);
			if (lang !== void 0) htmlElement.setAttribute("lang", removeNullCharacters(lang, true));
		}
		#addImageInTextLayer(node, element) {
			const { alt, bbox, children } = node;
			const child = children?.[0];
			if (!this.#rawDims || !alt || !bbox || child?.type !== "content") return false;
			const { id } = child;
			if (!id) return false;
			element.setAttribute("aria-owns", id);
			const img = document.createElement("span");
			(this.#elementsToAddToTextLayer ||= /* @__PURE__ */ new Map()).set(id, img);
			img.setAttribute("role", "img");
			img.setAttribute("aria-label", removeNullCharacters(alt));
			const { pageHeight, pageX, pageY } = this.#rawDims;
			const calc = "calc(var(--scale-factor)*";
			const { style } = img;
			style.width = `${calc}${bbox[2] - bbox[0]}px)`;
			style.height = `${calc}${bbox[3] - bbox[1]}px)`;
			style.left = `${calc}${bbox[0] - pageX}px)`;
			style.top = `${calc}${pageHeight - bbox[3] + pageY}px)`;
			return true;
		}
		addElementsToTextLayer() {
			if (!this.#elementsToAddToTextLayer) return;
			for (const [id, img] of this.#elementsToAddToTextLayer) document.getElementById(id)?.append(img);
			this.#elementsToAddToTextLayer.clear();
			this.#elementsToAddToTextLayer = null;
		}
		#walk(node) {
			if (!node) return null;
			const element = document.createElement("span");
			if ("role" in node) {
				const { role } = node;
				const match = role.match(HEADING_PATTERN);
				if (match) {
					element.setAttribute("role", "heading");
					element.setAttribute("aria-level", match[1]);
				} else if (PDF_ROLE_TO_HTML_ROLE[role]) element.setAttribute("role", PDF_ROLE_TO_HTML_ROLE[role]);
				if (role === "Figure" && this.#addImageInTextLayer(node, element)) return element;
			}
			this.#setAttributes(node, element);
			if (node.children) {
				if (node.children.length === 1 && "id" in node.children[0]) this.#setAttributes(node.children[0], element);
				else for (const kid of node.children) element.append(this.#walk(kid));
			}
			return element;
		}
	};
	TextAccessibilityManager = class TextAccessibilityManager {
		#enabled = false;
		#textChildren = null;
		#textNodes = /* @__PURE__ */ new Map();
		#waitingElements = /* @__PURE__ */ new Map();
		setTextMapping(textDivs) {
			this.#textChildren = textDivs;
		}
		static #compareElementPositions(e1, e2) {
			const rect1 = e1.getBoundingClientRect();
			const rect2 = e2.getBoundingClientRect();
			if (rect1.width === 0 && rect1.height === 0) return 1;
			if (rect2.width === 0 && rect2.height === 0) return -1;
			const top1 = rect1.y;
			const bot1 = rect1.y + rect1.height;
			const mid1 = rect1.y + rect1.height / 2;
			const top2 = rect2.y;
			const bot2 = rect2.y + rect2.height;
			const mid2 = rect2.y + rect2.height / 2;
			if (mid1 <= top2 && mid2 >= bot1) return -1;
			if (mid2 <= top1 && mid1 >= bot2) return 1;
			return rect1.x + rect1.width / 2 - (rect2.x + rect2.width / 2);
		}
		enable() {
			if (this.#enabled) throw new Error("TextAccessibilityManager is already enabled.");
			if (!this.#textChildren) throw new Error("Text divs and strings have not been set.");
			this.#enabled = true;
			this.#textChildren = this.#textChildren.slice();
			this.#textChildren.sort(TextAccessibilityManager.#compareElementPositions);
			if (this.#textNodes.size > 0) {
				const textChildren = this.#textChildren;
				for (const [id, nodeIndex] of this.#textNodes) {
					if (!document.getElementById(id)) {
						this.#textNodes.delete(id);
						continue;
					}
					this.#addIdToAriaOwns(id, textChildren[nodeIndex]);
				}
			}
			for (const [element, isRemovable] of this.#waitingElements) this.addPointerInTextLayer(element, isRemovable);
			this.#waitingElements.clear();
		}
		disable() {
			if (!this.#enabled) return;
			this.#waitingElements.clear();
			this.#textChildren = null;
			this.#enabled = false;
		}
		removePointerInTextLayer(element) {
			if (!this.#enabled) {
				this.#waitingElements.delete(element);
				return;
			}
			const children = this.#textChildren;
			if (!children || children.length === 0) return;
			const { id } = element;
			const nodeIndex = this.#textNodes.get(id);
			if (nodeIndex === void 0) return;
			const node = children[nodeIndex];
			this.#textNodes.delete(id);
			let owns = node.getAttribute("aria-owns");
			if (owns?.includes(id)) {
				owns = owns.split(" ").filter((x) => x !== id).join(" ");
				if (owns) node.setAttribute("aria-owns", owns);
				else {
					node.removeAttribute("aria-owns");
					node.setAttribute("role", "presentation");
				}
			}
		}
		#addIdToAriaOwns(id, node) {
			const owns = node.getAttribute("aria-owns");
			if (!owns?.includes(id)) node.setAttribute("aria-owns", owns ? `${owns} ${id}` : id);
			node.removeAttribute("role");
		}
		addPointerInTextLayer(element, isRemovable) {
			const { id } = element;
			if (!id) return null;
			if (!this.#enabled) {
				this.#waitingElements.set(element, isRemovable);
				return null;
			}
			if (isRemovable) this.removePointerInTextLayer(element);
			const children = this.#textChildren;
			if (!children || children.length === 0) return null;
			const index = binarySearchFirstItem(children, (node) => TextAccessibilityManager.#compareElementPositions(element, node) < 0);
			const nodeIndex = Math.max(0, index - 1);
			const child = children[nodeIndex];
			this.#addIdToAriaOwns(id, child);
			this.#textNodes.set(id, nodeIndex);
			const parent = child.parentNode;
			return parent?.classList.contains("markedContent") ? parent.id : null;
		}
		moveElementInDOM(container, element, contentElement, isRemovable) {
			const id = this.addPointerInTextLayer(contentElement, isRemovable);
			if (!container.hasChildNodes()) {
				container.append(element);
				return id;
			}
			const children = Array.from(container.childNodes).filter((node) => node !== element);
			if (children.length === 0) return id;
			const elementToCompare = contentElement || element;
			const index = binarySearchFirstItem(children, (node) => TextAccessibilityManager.#compareElementPositions(elementToCompare, node) < 0);
			if (index === 0) children[0].before(element);
			else children[index - 1].after(element);
			return id;
		}
	};
	TextHighlighter = class {
		#eventAbortController = null;
		constructor({ findController, eventBus, pageIndex }) {
			this.findController = findController;
			this.matches = [];
			this.eventBus = eventBus;
			this.pageIdx = pageIndex;
			this.textDivs = null;
			this.textContentItemsStr = null;
			this.enabled = false;
		}
		setTextMapping(divs, texts) {
			this.textDivs = divs;
			this.textContentItemsStr = texts;
		}
		enable() {
			if (!this.textDivs || !this.textContentItemsStr) throw new Error("Text divs and strings have not been set.");
			if (this.enabled) throw new Error("TextHighlighter is already enabled.");
			this.enabled = true;
			if (!this.#eventAbortController) {
				this.#eventAbortController = new AbortController();
				this.eventBus._on("updatetextlayermatches", (evt) => {
					if (evt.pageIndex === this.pageIdx || evt.pageIndex === -1) this._updateMatches();
				}, { signal: this.#eventAbortController.signal });
			}
			this._updateMatches();
		}
		disable() {
			if (!this.enabled) return;
			this.enabled = false;
			this.#eventAbortController?.abort();
			this.#eventAbortController = null;
			this._updateMatches(true);
		}
		_convertMatches(matches, matchesLength) {
			if (!matches) return [];
			const { textContentItemsStr } = this;
			let i = 0, iIndex = 0;
			const end = textContentItemsStr.length - 1;
			const result = [];
			for (let m = 0, mm = matches.length; m < mm; m++) {
				let matchIdx = matches[m];
				while (i !== end && matchIdx >= iIndex + textContentItemsStr[i].length) {
					iIndex += textContentItemsStr[i].length;
					i++;
				}
				if (i === textContentItemsStr.length) console.error("Could not find a matching mapping");
				const match = { begin: {
					divIdx: i,
					offset: matchIdx - iIndex
				} };
				matchIdx += matchesLength[m];
				while (i !== end && matchIdx > iIndex + textContentItemsStr[i].length) {
					iIndex += textContentItemsStr[i].length;
					i++;
				}
				match.end = {
					divIdx: i,
					offset: matchIdx - iIndex
				};
				result.push(match);
			}
			return result;
		}
		_renderMatches(matches) {
			if (matches.length === 0) return;
			const { findController, pageIdx } = this;
			const { textContentItemsStr, textDivs } = this;
			const isSelectedPage = pageIdx === findController.selected.pageIdx;
			const selectedMatchIdx = findController.selected.matchIdx;
			const highlightAll = findController.state.highlightAll;
			let prevEnd = null;
			const infinity = {
				divIdx: -1,
				offset: void 0
			};
			function beginText(begin, className) {
				const divIdx = begin.divIdx;
				textDivs[divIdx].textContent = "";
				return appendTextToDiv(divIdx, 0, begin.offset, className);
			}
			function appendTextToDiv(divIdx, fromOffset, toOffset, className) {
				let div = textDivs[divIdx];
				if (div.nodeType === Node.TEXT_NODE) {
					const span = document.createElement("span");
					div.before(span);
					span.append(div);
					textDivs[divIdx] = span;
					div = span;
				}
				const content = textContentItemsStr[divIdx].substring(fromOffset, toOffset);
				const node = document.createTextNode(content);
				if (className) {
					const span = document.createElement("span");
					span.className = `${className} appended`;
					span.append(node);
					div.append(span);
					if (className.includes("selected")) {
						const { left } = span.getClientRects()[0];
						return left - div.getBoundingClientRect().left;
					}
					return 0;
				}
				div.append(node);
				return 0;
			}
			let i0 = selectedMatchIdx, i1 = i0 + 1;
			if (highlightAll) {
				i0 = 0;
				i1 = matches.length;
			} else if (!isSelectedPage) return;
			let lastDivIdx = -1;
			let lastOffset = -1;
			for (let i = i0; i < i1; i++) {
				const match = matches[i];
				const begin = match.begin;
				if (begin.divIdx === lastDivIdx && begin.offset === lastOffset) continue;
				lastDivIdx = begin.divIdx;
				lastOffset = begin.offset;
				const end = match.end;
				const isSelected = isSelectedPage && i === selectedMatchIdx;
				const highlightSuffix = isSelected ? " selected" : "";
				let selectedLeft = 0;
				if (!prevEnd || begin.divIdx !== prevEnd.divIdx) {
					if (prevEnd !== null) appendTextToDiv(prevEnd.divIdx, prevEnd.offset, infinity.offset);
					beginText(begin);
				} else appendTextToDiv(prevEnd.divIdx, prevEnd.offset, begin.offset);
				if (begin.divIdx === end.divIdx) selectedLeft = appendTextToDiv(begin.divIdx, begin.offset, end.offset, "highlight" + highlightSuffix);
				else {
					selectedLeft = appendTextToDiv(begin.divIdx, begin.offset, infinity.offset, "highlight begin" + highlightSuffix);
					for (let n0 = begin.divIdx + 1, n1 = end.divIdx; n0 < n1; n0++) textDivs[n0].className = "highlight middle" + highlightSuffix;
					beginText(end, "highlight end" + highlightSuffix);
				}
				prevEnd = end;
				if (isSelected) findController.scrollMatchIntoView({
					element: textDivs[begin.divIdx],
					selectedLeft,
					pageIndex: pageIdx,
					matchIndex: selectedMatchIdx
				});
			}
			if (prevEnd) appendTextToDiv(prevEnd.divIdx, prevEnd.offset, infinity.offset);
		}
		_updateMatches(reset = false) {
			if (!this.enabled && !reset) return;
			const { findController, matches, pageIdx } = this;
			const { textContentItemsStr, textDivs } = this;
			let clearedUntilDivIdx = -1;
			for (const match of matches) {
				const begin = Math.max(clearedUntilDivIdx, match.begin.divIdx);
				for (let n = begin, end = match.end.divIdx; n <= end; n++) {
					const div = textDivs[n];
					div.textContent = textContentItemsStr[n];
					div.className = "";
				}
				clearedUntilDivIdx = match.end.divIdx + 1;
			}
			if (!findController?.highlightMatches || reset) return;
			const pageMatches = findController.pageMatches[pageIdx] || null;
			const pageMatchesLength = findController.pageMatchesLength[pageIdx] || null;
			this.matches = this._convertMatches(pageMatches, pageMatchesLength);
			this._renderMatches(this.matches);
		}
	};
	TextLayerBuilder = class TextLayerBuilder {
		#enablePermissions = false;
		#onAppend = null;
		#renderingDone = false;
		#textLayer = null;
		static #textLayers = /* @__PURE__ */ new Map();
		static #selectionChangeAbortController = null;
		constructor({ pdfPage, highlighter = null, accessibilityManager = null, enablePermissions = false, onAppend = null }) {
			this.pdfPage = pdfPage;
			this.highlighter = highlighter;
			this.accessibilityManager = accessibilityManager;
			this.#enablePermissions = enablePermissions === true;
			this.#onAppend = onAppend;
			this.div = document.createElement("div");
			this.div.tabIndex = 0;
			this.div.className = "textLayer";
		}
		async render(viewport, textContentParams = null) {
			if (this.#renderingDone && this.#textLayer) {
				this.#textLayer.update({
					viewport,
					onBefore: this.hide.bind(this)
				});
				this.show();
				return;
			}
			this.cancel();
			this.#textLayer = new TextLayer({
				textContentSource: this.pdfPage.streamTextContent(textContentParams || {
					includeMarkedContent: true,
					disableNormalization: true
				}),
				container: this.div,
				viewport
			});
			const { textDivs, textContentItemsStr } = this.#textLayer;
			this.highlighter?.setTextMapping(textDivs, textContentItemsStr);
			this.accessibilityManager?.setTextMapping(textDivs);
			await this.#textLayer.render();
			this.#renderingDone = true;
			const endOfContent = document.createElement("div");
			endOfContent.className = "endOfContent";
			this.div.append(endOfContent);
			this.#bindMouse(endOfContent);
			this.#onAppend?.(this.div);
			this.highlighter?.enable();
			this.accessibilityManager?.enable();
		}
		hide() {
			if (!this.div.hidden && this.#renderingDone) {
				this.highlighter?.disable();
				this.div.hidden = true;
			}
		}
		show() {
			if (this.div.hidden && this.#renderingDone) {
				this.div.hidden = false;
				this.highlighter?.enable();
			}
		}
		cancel() {
			this.#textLayer?.cancel();
			this.#textLayer = null;
			this.highlighter?.disable();
			this.accessibilityManager?.disable();
			TextLayerBuilder.#removeGlobalSelectionListener(this.div);
		}
		#bindMouse(end) {
			const { div } = this;
			div.addEventListener("mousedown", () => {
				div.classList.add("selecting");
			});
			div.addEventListener("copy", (event) => {
				if (!this.#enablePermissions) {
					const selection = document.getSelection();
					event.clipboardData.setData("text/plain", removeNullCharacters(normalizeUnicode(selection.toString())));
				}
				stopEvent(event);
			});
			TextLayerBuilder.#textLayers.set(div, end);
			TextLayerBuilder.#enableGlobalSelectionListener();
		}
		static #removeGlobalSelectionListener(textLayerDiv) {
			this.#textLayers.delete(textLayerDiv);
			if (this.#textLayers.size === 0) {
				this.#selectionChangeAbortController?.abort();
				this.#selectionChangeAbortController = null;
			}
		}
		static #enableGlobalSelectionListener() {
			if (this.#selectionChangeAbortController) return;
			this.#selectionChangeAbortController = new AbortController();
			const { signal } = this.#selectionChangeAbortController;
			const reset = (end, textLayer) => {
				textLayer.append(end);
				end.style.width = "";
				end.style.height = "";
				textLayer.classList.remove("selecting");
			};
			let isPointerDown = false;
			document.addEventListener("pointerdown", () => {
				isPointerDown = true;
			}, { signal });
			document.addEventListener("pointerup", () => {
				isPointerDown = false;
				this.#textLayers.forEach(reset);
			}, { signal });
			window.addEventListener("blur", () => {
				isPointerDown = false;
				this.#textLayers.forEach(reset);
			}, { signal });
			document.addEventListener("keyup", () => {
				if (!isPointerDown) this.#textLayers.forEach(reset);
			}, { signal });
			var isFirefox, prevRange;
			document.addEventListener("selectionchange", () => {
				const selection = document.getSelection();
				if (selection.rangeCount === 0) {
					this.#textLayers.forEach(reset);
					return;
				}
				const activeTextLayers = /* @__PURE__ */ new Set();
				for (let i = 0; i < selection.rangeCount; i++) {
					const range = selection.getRangeAt(i);
					for (const textLayerDiv of this.#textLayers.keys()) if (!activeTextLayers.has(textLayerDiv) && range.intersectsNode(textLayerDiv)) activeTextLayers.add(textLayerDiv);
				}
				for (const [textLayerDiv, endDiv] of this.#textLayers) if (activeTextLayers.has(textLayerDiv)) textLayerDiv.classList.add("selecting");
				else reset(endDiv, textLayerDiv);
				isFirefox ??= getComputedStyle(this.#textLayers.values().next().value).getPropertyValue("-moz-user-select") === "none";
				if (isFirefox) return;
				const range = selection.getRangeAt(0);
				const modifyStart = prevRange && (range.compareBoundaryPoints(Range.END_TO_END, prevRange) === 0 || range.compareBoundaryPoints(Range.START_TO_END, prevRange) === 0);
				let anchor = modifyStart ? range.startContainer : range.endContainer;
				if (anchor.nodeType === Node.TEXT_NODE) anchor = anchor.parentNode;
				const parentTextLayer = anchor.parentElement?.closest(".textLayer");
				const endDiv = this.#textLayers.get(parentTextLayer);
				if (endDiv) {
					endDiv.style.width = parentTextLayer.style.width;
					endDiv.style.height = parentTextLayer.style.height;
					anchor.parentElement.insertBefore(endDiv, modifyStart ? anchor : anchor.nextSibling);
				}
				prevRange = range.cloneRange();
			}, { signal });
		}
	};
	XfaLayerBuilder = class {
		constructor({ pdfPage, annotationStorage = null, linkService, xfaHtml = null }) {
			this.pdfPage = pdfPage;
			this.annotationStorage = annotationStorage;
			this.linkService = linkService;
			this.xfaHtml = xfaHtml;
			this.div = null;
			this._cancelled = false;
		}
		async render(viewport, intent = "display") {
			if (intent === "print") {
				const parameters = {
					viewport: viewport.clone({ dontFlip: true }),
					div: this.div,
					xfaHtml: this.xfaHtml,
					annotationStorage: this.annotationStorage,
					linkService: this.linkService,
					intent
				};
				this.div = document.createElement("div");
				parameters.div = this.div;
				return XfaLayer.render(parameters);
			}
			const xfaHtml = await this.pdfPage.getXfa();
			if (this._cancelled || !xfaHtml) return { textDivs: [] };
			const parameters = {
				viewport: viewport.clone({ dontFlip: true }),
				div: this.div,
				xfaHtml,
				annotationStorage: this.annotationStorage,
				linkService: this.linkService,
				intent
			};
			if (this.div) return XfaLayer.update(parameters);
			this.div = document.createElement("div");
			parameters.div = this.div;
			return XfaLayer.render(parameters);
		}
		cancel() {
			this._cancelled = true;
		}
		hide() {
			if (!this.div) return;
			this.div.hidden = true;
		}
	};
	DEFAULT_LAYER_PROPERTIES = {
		annotationEditorUIManager: null,
		annotationStorage: null,
		downloadManager: null,
		enableScripting: false,
		fieldObjectsPromise: null,
		findController: null,
		hasJSActionsPromise: null,
		get linkService() {
			return new SimpleLinkService();
		}
	};
	LAYERS_ORDER = /* @__PURE__ */ new Map([
		["canvasWrapper", 0],
		["textLayer", 1],
		["annotationLayer", 2],
		["annotationEditorLayer", 3],
		["xfaLayer", 3]
	]);
	PDFPageView = class {
		#annotationMode = AnnotationMode.ENABLE_FORMS;
		#canvasWrapper = null;
		#enableHWA = false;
		#hasRestrictedScaling = false;
		#isEditing = false;
		#layerProperties = null;
		#loadingId = null;
		#originalViewport = null;
		#previousRotation = null;
		#scaleRoundX = 1;
		#scaleRoundY = 1;
		#renderError = null;
		#renderingState = RenderingStates.INITIAL;
		#textLayerMode = TextLayerMode.ENABLE;
		#useThumbnailCanvas = {
			directDrawing: true,
			initialOptionalContent: true,
			regularAnnotations: true
		};
		#layers = [
			null,
			null,
			null,
			null
		];
		constructor(options) {
			const container = options.container;
			const defaultViewport = options.defaultViewport;
			this.id = options.id;
			this.renderingId = "page" + this.id;
			this.#layerProperties = options.layerProperties || DEFAULT_LAYER_PROPERTIES;
			this.pdfPage = null;
			this.pageLabel = null;
			this.rotation = 0;
			this.scale = options.scale || DEFAULT_SCALE;
			this.viewport = defaultViewport;
			this.pdfPageRotate = defaultViewport.rotation;
			this._optionalContentConfigPromise = options.optionalContentConfigPromise || null;
			this.#textLayerMode = options.textLayerMode ?? TextLayerMode.ENABLE;
			this.#annotationMode = options.annotationMode ?? AnnotationMode.ENABLE_FORMS;
			this.imageResourcesPath = options.imageResourcesPath || "";
			this.maxCanvasPixels = options.maxCanvasPixels ?? AppOptions.get("maxCanvasPixels");
			this.pageColors = options.pageColors || null;
			this.#enableHWA = options.enableHWA || false;
			this.eventBus = options.eventBus;
			this.renderingQueue = options.renderingQueue;
			this.l10n = options.l10n;
			this.l10n ||= new genericl10n_GenericL10n();
			this.renderTask = null;
			this.resume = null;
			this._isStandalone = !this.renderingQueue?.hasViewer();
			this._container = container;
			this._annotationCanvasMap = null;
			this.annotationLayer = null;
			this.annotationEditorLayer = null;
			this.textLayer = null;
			this.xfaLayer = null;
			this.structTreeLayer = null;
			this.drawLayer = null;
			const div = document.createElement("div");
			div.className = "page";
			div.setAttribute("data-page-number", this.id);
			div.setAttribute("role", "region");
			div.setAttribute("data-l10n-id", "pdfjs-page-landmark");
			div.setAttribute("data-l10n-args", JSON.stringify({ page: this.id }));
			this.div = div;
			this.#setDimensions();
			container?.append(div);
			if (this._isStandalone) {
				container?.style.setProperty("--scale-factor", this.scale * PixelsPerInch.PDF_TO_CSS_UNITS);
				if (this.pageColors?.background) container?.style.setProperty("--page-bg-color", this.pageColors.background);
				const { optionalContentConfigPromise } = options;
				if (optionalContentConfigPromise) optionalContentConfigPromise.then((optionalContentConfig) => {
					if (optionalContentConfigPromise !== this._optionalContentConfigPromise) return;
					this.#useThumbnailCanvas.initialOptionalContent = optionalContentConfig.hasInitialVisibility;
				});
				if (!options.l10n) this.l10n.translate(this.div);
			}
		}
		#addLayer(div, name) {
			const pos = LAYERS_ORDER.get(name);
			const oldDiv = this.#layers[pos];
			this.#layers[pos] = div;
			if (oldDiv) {
				oldDiv.replaceWith(div);
				return;
			}
			for (let i = pos - 1; i >= 0; i--) {
				const layer = this.#layers[i];
				if (layer) {
					layer.after(div);
					return;
				}
			}
			this.div.prepend(div);
		}
		get renderingState() {
			return this.#renderingState;
		}
		set renderingState(state) {
			if (state === this.#renderingState) return;
			this.#renderingState = state;
			if (this.#loadingId) {
				clearTimeout(this.#loadingId);
				this.#loadingId = null;
			}
			switch (state) {
				case RenderingStates.PAUSED:
					this.div.classList.remove("loading");
					break;
				case RenderingStates.RUNNING:
					this.div.classList.add("loadingIcon");
					this.#loadingId = setTimeout(() => {
						this.div.classList.add("loading");
						this.#loadingId = null;
					}, 0);
					break;
				case RenderingStates.INITIAL:
				case RenderingStates.FINISHED: this.div.classList.remove("loadingIcon", "loading");
			}
		}
		#setDimensions() {
			const { viewport } = this;
			if (this.pdfPage) {
				if (this.#previousRotation === viewport.rotation) return;
				this.#previousRotation = viewport.rotation;
			}
			setLayerDimensions(this.div, viewport, true, false);
		}
		setPdfPage(pdfPage) {
			if (this._isStandalone && (this.pageColors?.foreground === "CanvasText" || this.pageColors?.background === "Canvas")) {
				this._container?.style.setProperty("--hcm-highlight-filter", pdfPage.filterFactory.addHighlightHCMFilter("highlight", "CanvasText", "Canvas", "HighlightText", "Highlight"));
				this._container?.style.setProperty("--hcm-highlight-selected-filter", pdfPage.filterFactory.addHighlightHCMFilter("highlight_selected", "CanvasText", "Canvas", "HighlightText", "Highlight"));
			}
			this.pdfPage = pdfPage;
			this.pdfPageRotate = pdfPage.rotate;
			const totalRotation = (this.rotation + this.pdfPageRotate) % 360;
			this.viewport = pdfPage.getViewport({
				scale: this.scale * PixelsPerInch.PDF_TO_CSS_UNITS,
				rotation: totalRotation
			});
			this.#setDimensions();
			this.reset();
		}
		destroy() {
			this.reset();
			this.pdfPage?.cleanup();
		}
		hasEditableAnnotations() {
			return !!this.annotationLayer?.hasEditableAnnotations();
		}
		get _textHighlighter() {
			return shadow(this, "_textHighlighter", new TextHighlighter({
				pageIndex: this.id - 1,
				eventBus: this.eventBus,
				findController: this.#layerProperties.findController
			}));
		}
		#dispatchLayerRendered(name, error) {
			this.eventBus.dispatch(name, {
				source: this,
				pageNumber: this.id,
				error
			});
		}
		async #renderAnnotationLayer() {
			let error = null;
			try {
				await this.annotationLayer.render(this.viewport, { structTreeLayer: this.structTreeLayer }, "display");
			} catch (ex) {
				console.error("#renderAnnotationLayer:", ex);
				error = ex;
			} finally {
				this.#dispatchLayerRendered("annotationlayerrendered", error);
			}
		}
		async #renderAnnotationEditorLayer() {
			let error = null;
			try {
				await this.annotationEditorLayer.render(this.viewport, "display");
			} catch (ex) {
				console.error("#renderAnnotationEditorLayer:", ex);
				error = ex;
			} finally {
				this.#dispatchLayerRendered("annotationeditorlayerrendered", error);
			}
		}
		async #renderDrawLayer() {
			try {
				await this.drawLayer.render("display");
			} catch (ex) {
				console.error("#renderDrawLayer:", ex);
			}
		}
		async #renderXfaLayer() {
			let error = null;
			try {
				const result = await this.xfaLayer.render(this.viewport, "display");
				if (result?.textDivs && this._textHighlighter) this.#buildXfaTextContentItems(result.textDivs);
			} catch (ex) {
				console.error("#renderXfaLayer:", ex);
				error = ex;
			} finally {
				if (this.xfaLayer?.div) {
					this.l10n.pause();
					this.#addLayer(this.xfaLayer.div, "xfaLayer");
					this.l10n.resume();
				}
				this.#dispatchLayerRendered("xfalayerrendered", error);
			}
		}
		async #renderTextLayer() {
			if (!this.textLayer) return;
			let error = null;
			try {
				await this.textLayer.render(this.viewport);
			} catch (ex) {
				if (ex instanceof AbortException) return;
				console.error("#renderTextLayer:", ex);
				error = ex;
			}
			this.#dispatchLayerRendered("textlayerrendered", error);
			this.#renderStructTreeLayer();
		}
		async #renderStructTreeLayer() {
			if (!this.textLayer) return;
			const treeDom = await this.structTreeLayer?.render();
			if (treeDom) {
				this.l10n.pause();
				this.structTreeLayer?.addElementsToTextLayer();
				if (this.canvas && treeDom.parentNode !== this.canvas) this.canvas.append(treeDom);
				this.l10n.resume();
			}
			this.structTreeLayer?.show();
		}
		async #buildXfaTextContentItems(textDivs) {
			const text = await this.pdfPage.getTextContent();
			const items = [];
			for (const item of text.items) items.push(item.str);
			this._textHighlighter.setTextMapping(textDivs, items);
			this._textHighlighter.enable();
		}
		#resetCanvas() {
			const { canvas } = this;
			if (!canvas) return;
			canvas.remove();
			canvas.width = canvas.height = 0;
			this.canvas = null;
			this.#originalViewport = null;
		}
		reset({ keepAnnotationLayer = false, keepAnnotationEditorLayer = false, keepXfaLayer = false, keepTextLayer = false, keepCanvasWrapper = false } = {}) {
			this.cancelRendering({
				keepAnnotationLayer,
				keepAnnotationEditorLayer,
				keepXfaLayer,
				keepTextLayer
			});
			this.renderingState = RenderingStates.INITIAL;
			const div = this.div;
			const childNodes = div.childNodes, annotationLayerNode = keepAnnotationLayer && this.annotationLayer?.div || null, annotationEditorLayerNode = keepAnnotationEditorLayer && this.annotationEditorLayer?.div || null, xfaLayerNode = keepXfaLayer && this.xfaLayer?.div || null, textLayerNode = keepTextLayer && this.textLayer?.div || null, canvasWrapperNode = keepCanvasWrapper && this.#canvasWrapper || null;
			for (let i = childNodes.length - 1; i >= 0; i--) {
				const node = childNodes[i];
				switch (node) {
					case annotationLayerNode:
					case annotationEditorLayerNode:
					case xfaLayerNode:
					case textLayerNode:
					case canvasWrapperNode: continue;
				}
				node.remove();
				const layerIndex = this.#layers.indexOf(node);
				if (layerIndex >= 0) this.#layers[layerIndex] = null;
			}
			div.removeAttribute("data-loaded");
			if (annotationLayerNode) this.annotationLayer.hide();
			if (annotationEditorLayerNode) this.annotationEditorLayer.hide();
			if (xfaLayerNode) this.xfaLayer.hide();
			if (textLayerNode) this.textLayer.hide();
			this.structTreeLayer?.hide();
			if (!keepCanvasWrapper && this.#canvasWrapper) {
				this.#canvasWrapper = null;
				this.#resetCanvas();
			}
		}
		toggleEditingMode(isEditing) {
			if (!this.hasEditableAnnotations()) return;
			this.#isEditing = isEditing;
			this.reset({
				keepAnnotationLayer: true,
				keepAnnotationEditorLayer: true,
				keepXfaLayer: true,
				keepTextLayer: true,
				keepCanvasWrapper: true
			});
		}
		update({ scale = 0, rotation = null, optionalContentConfigPromise = null, drawingDelay = -1 }) {
			this.scale = scale || this.scale;
			if (typeof rotation === "number") this.rotation = rotation;
			if (optionalContentConfigPromise instanceof Promise) {
				this._optionalContentConfigPromise = optionalContentConfigPromise;
				optionalContentConfigPromise.then((optionalContentConfig) => {
					if (optionalContentConfigPromise !== this._optionalContentConfigPromise) return;
					this.#useThumbnailCanvas.initialOptionalContent = optionalContentConfig.hasInitialVisibility;
				});
			}
			this.#useThumbnailCanvas.directDrawing = true;
			const totalRotation = (this.rotation + this.pdfPageRotate) % 360;
			this.viewport = this.viewport.clone({
				scale: this.scale * PixelsPerInch.PDF_TO_CSS_UNITS,
				rotation: totalRotation
			});
			this.#setDimensions();
			if (this._isStandalone) this._container?.style.setProperty("--scale-factor", this.viewport.scale);
			if (this.canvas) {
				let onlyCssZoom = false;
				if (this.#hasRestrictedScaling) {
					if (this.maxCanvasPixels === 0) onlyCssZoom = true;
					else if (this.maxCanvasPixels > 0) {
						const { width, height } = this.viewport;
						const { sx, sy } = this.outputScale;
						onlyCssZoom = (Math.floor(width) * sx | 0) * (Math.floor(height) * sy | 0) > this.maxCanvasPixels;
					}
				}
				const postponeDrawing = drawingDelay >= 0 && drawingDelay < 1e3;
				if (postponeDrawing || onlyCssZoom) {
					if (postponeDrawing && !onlyCssZoom && this.renderingState !== RenderingStates.FINISHED) {
						this.cancelRendering({
							keepAnnotationLayer: true,
							keepAnnotationEditorLayer: true,
							keepXfaLayer: true,
							keepTextLayer: true,
							cancelExtraDelay: drawingDelay
						});
						this.renderingState = RenderingStates.FINISHED;
						this.#useThumbnailCanvas.directDrawing = false;
					}
					this.cssTransform({
						redrawAnnotationLayer: true,
						redrawAnnotationEditorLayer: true,
						redrawXfaLayer: true,
						redrawTextLayer: !postponeDrawing,
						hideTextLayer: postponeDrawing
					});
					if (postponeDrawing) return;
					this.eventBus.dispatch("pagerendered", {
						source: this,
						pageNumber: this.id,
						cssTransform: true,
						timestamp: performance.now(),
						error: this.#renderError
					});
					return;
				}
			}
			this.cssTransform({});
			this.reset({
				keepAnnotationLayer: true,
				keepAnnotationEditorLayer: true,
				keepXfaLayer: true,
				keepTextLayer: true,
				keepCanvasWrapper: true
			});
		}
		cancelRendering({ keepAnnotationLayer = false, keepAnnotationEditorLayer = false, keepXfaLayer = false, keepTextLayer = false, cancelExtraDelay = 0 } = {}) {
			if (this.renderTask) {
				this.renderTask.cancel(cancelExtraDelay);
				this.renderTask = null;
			}
			this.resume = null;
			if (this.textLayer && (!keepTextLayer || !this.textLayer.div)) {
				this.textLayer.cancel();
				this.textLayer = null;
			}
			if (this.annotationLayer && (!keepAnnotationLayer || !this.annotationLayer.div)) {
				this.annotationLayer.cancel();
				this.annotationLayer = null;
				this._annotationCanvasMap = null;
			}
			if (this.structTreeLayer && !this.textLayer) this.structTreeLayer = null;
			if (this.annotationEditorLayer && (!keepAnnotationEditorLayer || !this.annotationEditorLayer.div)) {
				if (this.drawLayer) {
					this.drawLayer.cancel();
					this.drawLayer = null;
				}
				this.annotationEditorLayer.cancel();
				this.annotationEditorLayer = null;
			}
			if (this.xfaLayer && (!keepXfaLayer || !this.xfaLayer.div)) {
				this.xfaLayer.cancel();
				this.xfaLayer = null;
				this._textHighlighter?.disable();
			}
		}
		cssTransform({ redrawAnnotationLayer = false, redrawAnnotationEditorLayer = false, redrawXfaLayer = false, redrawTextLayer = false, hideTextLayer = false }) {
			const { canvas } = this;
			if (!canvas) return;
			const originalViewport = this.#originalViewport;
			if (this.viewport !== originalViewport) {
				const relativeRotation = (360 + this.viewport.rotation - originalViewport.rotation) % 360;
				if (relativeRotation === 90 || relativeRotation === 270) {
					const { width, height } = this.viewport;
					const scaleX = height / width;
					const scaleY = width / height;
					canvas.style.transform = `rotate(${relativeRotation}deg) scale(${scaleX},${scaleY})`;
				} else canvas.style.transform = relativeRotation === 0 ? "" : `rotate(${relativeRotation}deg)`;
			}
			if (redrawAnnotationLayer && this.annotationLayer) this.#renderAnnotationLayer();
			if (redrawAnnotationEditorLayer && this.annotationEditorLayer) {
				if (this.drawLayer) this.#renderDrawLayer();
				this.#renderAnnotationEditorLayer();
			}
			if (redrawXfaLayer && this.xfaLayer) this.#renderXfaLayer();
			if (this.textLayer) {
				if (hideTextLayer) {
					this.textLayer.hide();
					this.structTreeLayer?.hide();
				} else if (redrawTextLayer) this.#renderTextLayer();
			}
		}
		get width() {
			return this.viewport.width;
		}
		get height() {
			return this.viewport.height;
		}
		getPagePoint(x, y) {
			return this.viewport.convertToPdfPoint(x, y);
		}
		async #finishRenderTask(renderTask, error = null) {
			if (renderTask === this.renderTask) this.renderTask = null;
			if (error instanceof RenderingCancelledException) {
				this.#renderError = null;
				return;
			}
			this.#renderError = error;
			this.renderingState = RenderingStates.FINISHED;
			this.#useThumbnailCanvas.regularAnnotations = !renderTask.separateAnnots;
			this.eventBus.dispatch("pagerendered", {
				source: this,
				pageNumber: this.id,
				cssTransform: false,
				timestamp: performance.now(),
				error: this.#renderError
			});
			if (error) throw error;
		}
		async draw() {
			if (this.renderingState !== RenderingStates.INITIAL) {
				console.error("Must be in new state before drawing");
				this.reset();
			}
			const { div, l10n, pageColors, pdfPage, viewport } = this;
			if (!pdfPage) {
				this.renderingState = RenderingStates.FINISHED;
				throw new Error("pdfPage is not loaded");
			}
			this.renderingState = RenderingStates.RUNNING;
			let canvasWrapper = this.#canvasWrapper;
			if (!canvasWrapper) {
				canvasWrapper = this.#canvasWrapper = document.createElement("div");
				canvasWrapper.classList.add("canvasWrapper");
				this.#addLayer(canvasWrapper, "canvasWrapper");
			}
			if (!this.textLayer && this.#textLayerMode !== TextLayerMode.DISABLE && !pdfPage.isPureXfa) {
				this._accessibilityManager ||= new TextAccessibilityManager();
				this.textLayer = new TextLayerBuilder({
					pdfPage,
					highlighter: this._textHighlighter,
					accessibilityManager: this._accessibilityManager,
					enablePermissions: this.#textLayerMode === TextLayerMode.ENABLE_PERMISSIONS,
					onAppend: (textLayerDiv) => {
						this.l10n.pause();
						this.#addLayer(textLayerDiv, "textLayer");
						this.l10n.resume();
					}
				});
			}
			if (!this.annotationLayer && this.#annotationMode !== AnnotationMode.DISABLE) {
				const { annotationStorage, annotationEditorUIManager, downloadManager, enableScripting, fieldObjectsPromise, hasJSActionsPromise, linkService } = this.#layerProperties;
				this._annotationCanvasMap ||= /* @__PURE__ */ new Map();
				this.annotationLayer = new AnnotationLayerBuilder({
					pdfPage,
					annotationStorage,
					imageResourcesPath: this.imageResourcesPath,
					renderForms: this.#annotationMode === AnnotationMode.ENABLE_FORMS,
					linkService,
					downloadManager,
					enableScripting,
					hasJSActionsPromise,
					fieldObjectsPromise,
					annotationCanvasMap: this._annotationCanvasMap,
					accessibilityManager: this._accessibilityManager,
					annotationEditorUIManager,
					onAppend: (annotationLayerDiv) => {
						this.#addLayer(annotationLayerDiv, "annotationLayer");
					}
				});
			}
			const renderContinueCallback = (cont) => {
				showCanvas?.(false);
				if (this.renderingQueue && !this.renderingQueue.isHighestPriority(this)) {
					this.renderingState = RenderingStates.PAUSED;
					this.resume = () => {
						this.renderingState = RenderingStates.RUNNING;
						cont();
					};
					return;
				}
				cont();
			};
			const { width, height } = viewport;
			const canvas = document.createElement("canvas");
			canvas.setAttribute("role", "presentation");
			const hasHCM = !!(pageColors?.background && pageColors?.foreground);
			const prevCanvas = this.canvas;
			const updateOnFirstShow = !prevCanvas && !hasHCM;
			this.canvas = canvas;
			this.#originalViewport = viewport;
			let showCanvas = (isLastShow) => {
				if (updateOnFirstShow) {
					canvasWrapper.prepend(canvas);
					showCanvas = null;
					return;
				}
				if (!isLastShow) return;
				if (prevCanvas) {
					prevCanvas.replaceWith(canvas);
					prevCanvas.width = prevCanvas.height = 0;
				} else canvasWrapper.prepend(canvas);
				showCanvas = null;
			};
			const ctx = canvas.getContext("2d", {
				alpha: false,
				willReadFrequently: !this.#enableHWA
			});
			const outputScale = this.outputScale = new OutputScale();
			if (this.maxCanvasPixels === 0) {
				const invScale = 1 / this.scale;
				outputScale.sx *= invScale;
				outputScale.sy *= invScale;
				this.#hasRestrictedScaling = true;
			} else if (this.maxCanvasPixels > 0) {
				const pixelsInViewport = width * height;
				const maxScale = Math.sqrt(this.maxCanvasPixels / pixelsInViewport);
				if (outputScale.sx > maxScale || outputScale.sy > maxScale) {
					outputScale.sx = maxScale;
					outputScale.sy = maxScale;
					this.#hasRestrictedScaling = true;
				} else this.#hasRestrictedScaling = false;
			}
			const sfx = approximateFraction(outputScale.sx);
			const sfy = approximateFraction(outputScale.sy);
			const canvasWidth = canvas.width = floorToDivide(calcRound(width * outputScale.sx), sfx[0]);
			const canvasHeight = canvas.height = floorToDivide(calcRound(height * outputScale.sy), sfy[0]);
			const pageWidth = floorToDivide(calcRound(width), sfx[1]);
			const pageHeight = floorToDivide(calcRound(height), sfy[1]);
			outputScale.sx = canvasWidth / pageWidth;
			outputScale.sy = canvasHeight / pageHeight;
			if (this.#scaleRoundX !== sfx[1]) {
				div.style.setProperty("--scale-round-x", `${sfx[1]}px`);
				this.#scaleRoundX = sfx[1];
			}
			if (this.#scaleRoundY !== sfy[1]) {
				div.style.setProperty("--scale-round-y", `${sfy[1]}px`);
				this.#scaleRoundY = sfy[1];
			}
			const renderContext = {
				canvasContext: ctx,
				transform: outputScale.scaled ? [
					outputScale.sx,
					0,
					0,
					outputScale.sy,
					0,
					0
				] : null,
				viewport,
				annotationMode: this.#annotationMode,
				optionalContentConfigPromise: this._optionalContentConfigPromise,
				annotationCanvasMap: this._annotationCanvasMap,
				pageColors,
				isEditing: this.#isEditing
			};
			const renderTask = this.renderTask = pdfPage.render(renderContext);
			renderTask.onContinue = renderContinueCallback;
			const resultPromise = renderTask.promise.then(async () => {
				showCanvas?.(true);
				await this.#finishRenderTask(renderTask);
				this.structTreeLayer ||= new StructTreeLayerBuilder(pdfPage, viewport.rawDims);
				this.#renderTextLayer();
				if (this.annotationLayer) await this.#renderAnnotationLayer();
				const { annotationEditorUIManager } = this.#layerProperties;
				if (!annotationEditorUIManager) return;
				this.drawLayer ||= new DrawLayerBuilder({ pageIndex: this.id });
				await this.#renderDrawLayer();
				this.drawLayer.setParent(canvasWrapper);
				this.annotationEditorLayer ||= new AnnotationEditorLayerBuilder({
					uiManager: annotationEditorUIManager,
					pdfPage,
					l10n,
					structTreeLayer: this.structTreeLayer,
					accessibilityManager: this._accessibilityManager,
					annotationLayer: this.annotationLayer?.annotationLayer,
					textLayer: this.textLayer,
					drawLayer: this.drawLayer.getDrawLayer(),
					onAppend: (annotationEditorLayerDiv) => {
						this.#addLayer(annotationEditorLayerDiv, "annotationEditorLayer");
					}
				});
				this.#renderAnnotationEditorLayer();
			}, (error) => {
				if (!(error instanceof RenderingCancelledException)) showCanvas?.(true);
				else {
					prevCanvas?.remove();
					this.#resetCanvas();
				}
				return this.#finishRenderTask(renderTask, error);
			});
			if (pdfPage.isPureXfa) {
				if (!this.xfaLayer) {
					const { annotationStorage, linkService } = this.#layerProperties;
					this.xfaLayer = new XfaLayerBuilder({
						pdfPage,
						annotationStorage,
						linkService
					});
				}
				this.#renderXfaLayer();
			}
			div.setAttribute("data-loaded", true);
			this.eventBus.dispatch("pagerender", {
				source: this,
				pageNumber: this.id
			});
			return resultPromise;
		}
		setPageLabel(label) {
			this.pageLabel = typeof label === "string" ? label : null;
			this.div.setAttribute("data-l10n-args", JSON.stringify({ page: this.pageLabel ?? this.id }));
			if (this.pageLabel !== null) this.div.setAttribute("data-page-label", this.pageLabel);
			else this.div.removeAttribute("data-page-label");
		}
		get thumbnailCanvas() {
			const { directDrawing, initialOptionalContent, regularAnnotations } = this.#useThumbnailCanvas;
			return directDrawing && initialOptionalContent && regularAnnotations ? this.canvas : null;
		}
	};
	GenericScripting = class {
		constructor(sandboxBundleSrc) {
			this._ready = Promise.reject(/* @__PURE__ */ new Error("PDF.js scripting sandbox is not packaged."));
		}
		async createSandbox(data) {
			(await this._ready).create(data);
		}
		async dispatchEventInSandbox(event) {
			const sandbox = await this._ready;
			setTimeout(() => sandbox.dispatchEvent(event), 0);
		}
		async destroySandbox() {
			(await this._ready).nukeSandbox();
		}
	};
	PDFScriptingManager = class {
		#closeCapability = null;
		#destroyCapability = null;
		#docProperties = null;
		#eventAbortController = null;
		#eventBus = null;
		#externalServices = null;
		#pdfDocument = null;
		#pdfViewer = null;
		#ready = false;
		#scripting = null;
		#willPrintCapability = null;
		constructor({ eventBus, externalServices = null, docProperties = null }) {
			this.#eventBus = eventBus;
			this.#externalServices = externalServices;
			this.#docProperties = docProperties;
		}
		setViewer(pdfViewer) {
			this.#pdfViewer = pdfViewer;
		}
		async setDocument(pdfDocument) {
			if (this.#pdfDocument) await this.#destroyScripting();
			this.#pdfDocument = pdfDocument;
			if (!pdfDocument) return;
			const [objects, calculationOrder, docActions] = await Promise.all([
				pdfDocument.getFieldObjects(),
				pdfDocument.getCalculationOrderIds(),
				pdfDocument.getJSActions()
			]);
			if (!objects && !docActions) {
				await this.#destroyScripting();
				return;
			}
			if (pdfDocument !== this.#pdfDocument) return;
			try {
				this.#scripting = this.#initScripting();
			} catch (error) {
				console.error("setDocument:", error);
				await this.#destroyScripting();
				return;
			}
			const eventBus = this.#eventBus;
			this.#eventAbortController = new AbortController();
			const { signal } = this.#eventAbortController;
			eventBus._on("updatefromsandbox", (event) => {
				if (event?.source === window) this.#updateFromSandbox(event.detail);
			}, { signal });
			eventBus._on("dispatcheventinsandbox", (event) => {
				this.#scripting?.dispatchEventInSandbox(event.detail);
			}, { signal });
			eventBus._on("pagechanging", ({ pageNumber, previous }) => {
				if (pageNumber === previous) return;
				this.#dispatchPageClose(previous);
				this.#dispatchPageOpen(pageNumber);
			}, { signal });
			eventBus._on("pagerendered", ({ pageNumber }) => {
				if (!this._pageOpenPending.has(pageNumber)) return;
				if (pageNumber !== this.#pdfViewer.currentPageNumber) return;
				this.#dispatchPageOpen(pageNumber);
			}, { signal });
			eventBus._on("pagesdestroy", async () => {
				await this.#dispatchPageClose(this.#pdfViewer.currentPageNumber);
				await this.#scripting?.dispatchEventInSandbox({
					id: "doc",
					name: "WillClose"
				});
				this.#closeCapability?.resolve();
			}, { signal });
			try {
				const docProperties = await this.#docProperties(pdfDocument);
				if (pdfDocument !== this.#pdfDocument) return;
				await this.#scripting.createSandbox({
					objects,
					calculationOrder,
					appInfo: {
						platform: navigator.platform,
						language: navigator.language
					},
					docInfo: {
						...docProperties,
						actions: docActions
					}
				});
				eventBus.dispatch("sandboxcreated", { source: this });
			} catch (error) {
				console.error("setDocument:", error);
				await this.#destroyScripting();
				return;
			}
			await this.#scripting?.dispatchEventInSandbox({
				id: "doc",
				name: "Open"
			});
			await this.#dispatchPageOpen(this.#pdfViewer.currentPageNumber, true);
			Promise.resolve().then(() => {
				if (pdfDocument === this.#pdfDocument) this.#ready = true;
			});
		}
		async dispatchWillSave() {
			return this.#scripting?.dispatchEventInSandbox({
				id: "doc",
				name: "WillSave"
			});
		}
		async dispatchDidSave() {
			return this.#scripting?.dispatchEventInSandbox({
				id: "doc",
				name: "DidSave"
			});
		}
		async dispatchWillPrint() {
			if (!this.#scripting) return;
			await this.#willPrintCapability?.promise;
			this.#willPrintCapability = Promise.withResolvers();
			try {
				await this.#scripting.dispatchEventInSandbox({
					id: "doc",
					name: "WillPrint"
				});
			} catch (ex) {
				this.#willPrintCapability.resolve();
				this.#willPrintCapability = null;
				throw ex;
			}
			await this.#willPrintCapability.promise;
		}
		async dispatchDidPrint() {
			return this.#scripting?.dispatchEventInSandbox({
				id: "doc",
				name: "DidPrint"
			});
		}
		get destroyPromise() {
			return this.#destroyCapability?.promise || null;
		}
		get ready() {
			return this.#ready;
		}
		get _pageOpenPending() {
			return shadow(this, "_pageOpenPending", /* @__PURE__ */ new Set());
		}
		get _visitedPages() {
			return shadow(this, "_visitedPages", /* @__PURE__ */ new Map());
		}
		async #updateFromSandbox(detail) {
			const pdfViewer = this.#pdfViewer;
			const isInPresentationMode = pdfViewer.isInPresentationMode || pdfViewer.isChangingPresentationMode;
			const { id, siblings, command, value } = detail;
			if (!id) {
				switch (command) {
					case "clear":
						console.clear();
						break;
					case "error":
						console.error(value);
						break;
					case "layout":
						if (!isInPresentationMode) pdfViewer.spreadMode = apiPageLayoutToViewerModes(value).spreadMode;
						break;
					case "page-num":
						pdfViewer.currentPageNumber = value + 1;
						break;
					case "print":
						await pdfViewer.pagesPromise;
						this.#eventBus.dispatch("print", { source: this });
						break;
					case "println":
						console.log(value);
						break;
					case "zoom":
						if (!isInPresentationMode) pdfViewer.currentScaleValue = value;
						break;
					case "SaveAs":
						this.#eventBus.dispatch("download", { source: this });
						break;
					case "FirstPage":
						pdfViewer.currentPageNumber = 1;
						break;
					case "LastPage":
						pdfViewer.currentPageNumber = pdfViewer.pagesCount;
						break;
					case "NextPage":
						pdfViewer.nextPage();
						break;
					case "PrevPage":
						pdfViewer.previousPage();
						break;
					case "ZoomViewIn":
						if (!isInPresentationMode) pdfViewer.increaseScale();
						break;
					case "ZoomViewOut":
						if (!isInPresentationMode) pdfViewer.decreaseScale();
						break;
					case "WillPrintFinished":
						this.#willPrintCapability?.resolve();
						this.#willPrintCapability = null;
				}
				return;
			}
			if (isInPresentationMode && detail.focus) return;
			delete detail.id;
			delete detail.siblings;
			const ids = siblings ? [id, ...siblings] : [id];
			for (const elementId of ids) {
				const element = document.querySelector(`[data-element-id="${elementId}"]`);
				if (element) element.dispatchEvent(new CustomEvent("updatefromsandbox", { detail }));
				else this.#pdfDocument?.annotationStorage.setValue(elementId, detail);
			}
		}
		async #dispatchPageOpen(pageNumber, initialize = false) {
			const pdfDocument = this.#pdfDocument, visitedPages = this._visitedPages;
			if (initialize) this.#closeCapability = Promise.withResolvers();
			if (!this.#closeCapability) return;
			const pageView = this.#pdfViewer.getPageView(pageNumber - 1);
			if (pageView?.renderingState !== RenderingStates.FINISHED) {
				this._pageOpenPending.add(pageNumber);
				return;
			}
			this._pageOpenPending.delete(pageNumber);
			const actionsPromise = (async () => {
				const actions = await (!visitedPages.has(pageNumber) ? pageView.pdfPage?.getJSActions() : null);
				if (pdfDocument !== this.#pdfDocument) return;
				await this.#scripting?.dispatchEventInSandbox({
					id: "page",
					name: "PageOpen",
					pageNumber,
					actions
				});
			})();
			visitedPages.set(pageNumber, actionsPromise);
		}
		async #dispatchPageClose(pageNumber) {
			const pdfDocument = this.#pdfDocument, visitedPages = this._visitedPages;
			if (!this.#closeCapability) return;
			if (this._pageOpenPending.has(pageNumber)) return;
			const actionsPromise = visitedPages.get(pageNumber);
			if (!actionsPromise) return;
			visitedPages.set(pageNumber, null);
			await actionsPromise;
			if (pdfDocument !== this.#pdfDocument) return;
			await this.#scripting?.dispatchEventInSandbox({
				id: "page",
				name: "PageClose",
				pageNumber
			});
		}
		#initScripting() {
			this.#destroyCapability = Promise.withResolvers();
			if (this.#scripting) throw new Error("#initScripting: Scripting already exists.");
			return this.#externalServices.createScripting();
		}
		async #destroyScripting() {
			if (!this.#scripting) {
				this.#pdfDocument = null;
				this.#destroyCapability?.resolve();
				return;
			}
			if (this.#closeCapability) {
				await Promise.race([this.#closeCapability.promise, new Promise((resolve) => {
					setTimeout(resolve, 1e3);
				})]).catch(() => {});
				this.#closeCapability = null;
			}
			this.#pdfDocument = null;
			try {
				await this.#scripting.destroySandbox();
			} catch {}
			this.#willPrintCapability?.reject(/* @__PURE__ */ new Error("Scripting destroyed."));
			this.#willPrintCapability = null;
			this.#eventAbortController?.abort();
			this.#eventAbortController = null;
			this._pageOpenPending.clear();
			this._visitedPages.clear();
			this.#scripting = null;
			this.#ready = false;
			this.#destroyCapability?.resolve();
		}
	};
	PDFScriptingManagerComponents = class extends PDFScriptingManager {
		constructor(options) {
			if (!options.externalServices) window.addEventListener("updatefromsandbox", (event) => {
				options.eventBus.dispatch("updatefromsandbox", {
					source: window,
					detail: event.detail
				});
			});
			options.externalServices ||= { createScripting: () => new GenericScripting(options.sandboxBundleSrc) };
			options.docProperties ||= (pdfDocument) => docProperties(pdfDocument);
			super(options);
		}
	};
	CLEANUP_TIMEOUT = 3e4;
	PDFRenderingQueue$1 = class {
		constructor() {
			this.pdfViewer = null;
			this.pdfThumbnailViewer = null;
			this.onIdle = null;
			this.highestPriorityPage = null;
			this.idleTimeout = null;
			this.printing = false;
			this.isThumbnailViewEnabled = false;
			Object.defineProperty(this, "hasViewer", { value: () => !!this.pdfViewer });
		}
		setViewer(pdfViewer) {
			this.pdfViewer = pdfViewer;
		}
		setThumbnailViewer(pdfThumbnailViewer) {
			this.pdfThumbnailViewer = pdfThumbnailViewer;
		}
		isHighestPriority(view) {
			return this.highestPriorityPage === view.renderingId;
		}
		renderHighestPriority(currentlyVisiblePages) {
			if (this.idleTimeout) {
				clearTimeout(this.idleTimeout);
				this.idleTimeout = null;
			}
			if (this.pdfViewer.forceRendering(currentlyVisiblePages)) return;
			if (this.isThumbnailViewEnabled && this.pdfThumbnailViewer?.forceRendering()) return;
			if (this.printing) return;
			if (this.onIdle) this.idleTimeout = setTimeout(this.onIdle.bind(this), CLEANUP_TIMEOUT);
		}
		getHighestPriority(visible, views, scrolledDown, preRenderExtra = false) {
			const visibleViews = visible.views, numVisible = visibleViews.length;
			if (numVisible === 0) return null;
			for (let i = 0; i < numVisible; i++) {
				const view = visibleViews[i].view;
				if (!this.isViewFinished(view)) return view;
			}
			const firstId = visible.first.id, lastId = visible.last.id;
			if (lastId - firstId + 1 > numVisible) {
				const visibleIds = visible.ids;
				for (let i = 1, ii = lastId - firstId; i < ii; i++) {
					const holeId = scrolledDown ? firstId + i : lastId - i;
					if (visibleIds.has(holeId)) continue;
					const holeView = views[holeId - 1];
					if (!this.isViewFinished(holeView)) return holeView;
				}
			}
			let preRenderIndex = scrolledDown ? lastId : firstId - 2;
			let preRenderView = views[preRenderIndex];
			if (preRenderView && !this.isViewFinished(preRenderView)) return preRenderView;
			if (preRenderExtra) {
				preRenderIndex += scrolledDown ? 1 : -1;
				preRenderView = views[preRenderIndex];
				if (preRenderView && !this.isViewFinished(preRenderView)) return preRenderView;
			}
			return null;
		}
		isViewFinished(view) {
			return view.renderingState === RenderingStates.FINISHED;
		}
		renderView(view) {
			switch (view.renderingState) {
				case RenderingStates.FINISHED: return false;
				case RenderingStates.PAUSED:
					this.highestPriorityPage = view.renderingId;
					view.resume();
					break;
				case RenderingStates.RUNNING:
					this.highestPriorityPage = view.renderingId;
					break;
				case RenderingStates.INITIAL:
					this.highestPriorityPage = view.renderingId;
					view.draw().finally(() => {
						this.renderHighestPriority();
					}).catch((reason) => {
						if (reason instanceof RenderingCancelledException) return;
						console.error("renderView:", reason);
					});
			}
			return true;
		}
	};
	DEFAULT_CACHE_SIZE = 10;
	PagesCountLimit = {
		FORCE_SCROLL_MODE_PAGE: 1e4,
		FORCE_LAZY_PAGE_INIT: 5e3,
		PAUSE_EAGER_PAGE_INIT: 250
	};
	PDFPageViewBuffer = class {
		#buf = /* @__PURE__ */ new Set();
		#size = 0;
		constructor(size) {
			this.#size = size;
		}
		push(view) {
			const buf = this.#buf;
			if (buf.has(view)) buf.delete(view);
			buf.add(view);
			if (buf.size > this.#size) this.#destroyFirstView();
		}
		resize(newSize, idsToKeep = null) {
			this.#size = newSize;
			const buf = this.#buf;
			if (idsToKeep) {
				const ii = buf.size;
				let i = 1;
				for (const view of buf) {
					if (idsToKeep.has(view.id)) {
						buf.delete(view);
						buf.add(view);
					}
					if (++i > ii) break;
				}
			}
			while (buf.size > this.#size) this.#destroyFirstView();
		}
		has(view) {
			return this.#buf.has(view);
		}
		[Symbol.iterator]() {
			return this.#buf.keys();
		}
		#destroyFirstView() {
			const firstView = this.#buf.keys().next().value;
			firstView?.destroy();
			this.#buf.delete(firstView);
		}
	};
	PDFViewer$1 = class {
		#buffer = null;
		#altTextManager = null;
		#annotationEditorHighlightColors = null;
		#annotationEditorMode = AnnotationEditorType.NONE;
		#annotationEditorUIManager = null;
		#annotationMode = AnnotationMode.ENABLE_FORMS;
		#containerTopLeft = null;
		#editorUndoBar = null;
		#enableHWA = false;
		#enableHighlightFloatingButton = false;
		#enablePermissions = false;
		#enableUpdatedAddImage = false;
		#enableNewAltTextWhenAddingImage = false;
		#eventAbortController = null;
		#mlManager = null;
		#switchAnnotationEditorModeAC = null;
		#switchAnnotationEditorModeTimeoutId = null;
		#getAllTextInProgress = false;
		#hiddenCopyElement = null;
		#interruptCopyCondition = false;
		#previousContainerHeight = 0;
		#resizeObserver = new ResizeObserver(this.#resizeObserverCallback.bind(this));
		#scrollModePageState = null;
		#scaleTimeoutId = null;
		#supportsPinchToZoom = true;
		#textLayerMode = TextLayerMode.ENABLE;
		constructor(options) {
			const viewerVersion = "4.10.38";
			if (version$1 !== viewerVersion) throw new Error(`The API version "${version$1}" does not match the Viewer version "${viewerVersion}".`);
			this.container = options.container;
			this.viewer = options.viewer || options.container.firstElementChild;
			if (this.container?.tagName !== "DIV" || this.viewer?.tagName !== "DIV") throw new Error("Invalid `container` and/or `viewer` option.");
			if (this.container.offsetParent && getComputedStyle(this.container).position !== "absolute") throw new Error("The `container` must be absolutely positioned.");
			this.#resizeObserver.observe(this.container);
			this.eventBus = options.eventBus;
			this.linkService = options.linkService || new SimpleLinkService();
			this.downloadManager = options.downloadManager || null;
			this.findController = options.findController || null;
			this.#altTextManager = options.altTextManager || null;
			this.#editorUndoBar = options.editorUndoBar || null;
			if (this.findController) this.findController.onIsPageVisible = (pageNumber) => this._getVisiblePages().ids.has(pageNumber);
			this._scriptingManager = options.scriptingManager || null;
			this.#textLayerMode = options.textLayerMode ?? TextLayerMode.ENABLE;
			this.#annotationMode = options.annotationMode ?? AnnotationMode.ENABLE_FORMS;
			this.#annotationEditorMode = options.annotationEditorMode ?? AnnotationEditorType.NONE;
			this.#annotationEditorHighlightColors = options.annotationEditorHighlightColors || null;
			this.#enableHighlightFloatingButton = options.enableHighlightFloatingButton === true;
			this.#enableUpdatedAddImage = options.enableUpdatedAddImage === true;
			this.#enableNewAltTextWhenAddingImage = options.enableNewAltTextWhenAddingImage === true;
			this.imageResourcesPath = options.imageResourcesPath || "";
			this.enablePrintAutoRotate = options.enablePrintAutoRotate || false;
			this.removePageBorders = options.removePageBorders || false;
			this.maxCanvasPixels = options.maxCanvasPixels;
			this.l10n = options.l10n;
			this.l10n ||= new genericl10n_GenericL10n();
			this.#enablePermissions = options.enablePermissions || false;
			this.pageColors = options.pageColors || null;
			this.#mlManager = options.mlManager || null;
			this.#enableHWA = options.enableHWA || false;
			this.#supportsPinchToZoom = options.supportsPinchToZoom !== false;
			this.defaultRenderingQueue = !options.renderingQueue;
			if (this.defaultRenderingQueue) {
				this.renderingQueue = new PDFRenderingQueue$1();
				this.renderingQueue.setViewer(this);
			} else this.renderingQueue = options.renderingQueue;
			const { abortSignal } = options;
			abortSignal?.addEventListener("abort", () => {
				this.#resizeObserver.disconnect();
				this.#resizeObserver = null;
			}, { once: true });
			this.scroll = watchScroll(this.container, this._scrollUpdate.bind(this), abortSignal);
			this.presentationModeState = PresentationModeState.UNKNOWN;
			this._resetView();
			if (this.removePageBorders) this.viewer.classList.add("removePageBorders");
			this.#updateContainerHeightCss();
			this.eventBus._on("thumbnailrendered", ({ pageNumber, pdfPage }) => {
				const pageView = this._pages[pageNumber - 1];
				if (!this.#buffer.has(pageView)) pdfPage?.cleanup();
			});
			if (!options.l10n) this.l10n.translate(this.container);
		}
		get pagesCount() {
			return this._pages.length;
		}
		getPageView(index) {
			return this._pages[index];
		}
		getCachedPageViews() {
			return new Set(this.#buffer);
		}
		get pageViewsReady() {
			return this._pages.every((pageView) => pageView?.pdfPage);
		}
		get renderForms() {
			return this.#annotationMode === AnnotationMode.ENABLE_FORMS;
		}
		get enableScripting() {
			return !!this._scriptingManager;
		}
		get currentPageNumber() {
			return this._currentPageNumber;
		}
		set currentPageNumber(val) {
			if (!Number.isInteger(val)) throw new Error("Invalid page number.");
			if (!this.pdfDocument) return;
			if (!this._setCurrentPageNumber(val, true)) console.error(`currentPageNumber: "${val}" is not a valid page.`);
		}
		_setCurrentPageNumber(val, resetCurrentPageView = false) {
			if (this._currentPageNumber === val) {
				if (resetCurrentPageView) this.#resetCurrentPageView();
				return true;
			}
			if (!(0 < val && val <= this.pagesCount)) return false;
			const previous = this._currentPageNumber;
			this._currentPageNumber = val;
			this.eventBus.dispatch("pagechanging", {
				source: this,
				pageNumber: val,
				pageLabel: this._pageLabels?.[val - 1] ?? null,
				previous
			});
			if (resetCurrentPageView) this.#resetCurrentPageView();
			return true;
		}
		get currentPageLabel() {
			return this._pageLabels?.[this._currentPageNumber - 1] ?? null;
		}
		set currentPageLabel(val) {
			if (!this.pdfDocument) return;
			let page = val | 0;
			if (this._pageLabels) {
				const i = this._pageLabels.indexOf(val);
				if (i >= 0) page = i + 1;
			}
			if (!this._setCurrentPageNumber(page, true)) console.error(`currentPageLabel: "${val}" is not a valid page.`);
		}
		get currentScale() {
			return this._currentScale !== UNKNOWN_SCALE ? this._currentScale : DEFAULT_SCALE;
		}
		set currentScale(val) {
			if (isNaN(val)) throw new Error("Invalid numeric scale.");
			if (!this.pdfDocument) return;
			this.#setScale(val, { noScroll: false });
		}
		get currentScaleValue() {
			return this._currentScaleValue;
		}
		set currentScaleValue(val) {
			if (!this.pdfDocument) return;
			this.#setScale(val, { noScroll: false });
		}
		get pagesRotation() {
			return this._pagesRotation;
		}
		set pagesRotation(rotation) {
			if (!isValidRotation(rotation)) throw new Error("Invalid pages rotation angle.");
			if (!this.pdfDocument) return;
			rotation %= 360;
			if (rotation < 0) rotation += 360;
			if (this._pagesRotation === rotation) return;
			this._pagesRotation = rotation;
			const pageNumber = this._currentPageNumber;
			this.refresh(true, { rotation });
			if (this._currentScaleValue) this.#setScale(this._currentScaleValue, { noScroll: true });
			this.eventBus.dispatch("rotationchanging", {
				source: this,
				pagesRotation: rotation,
				pageNumber
			});
			if (this.defaultRenderingQueue) this.update();
		}
		get firstPagePromise() {
			return this.pdfDocument ? this._firstPageCapability.promise : null;
		}
		get onePageRendered() {
			return this.pdfDocument ? this._onePageRenderedCapability.promise : null;
		}
		get pagesPromise() {
			return this.pdfDocument ? this._pagesCapability.promise : null;
		}
		get _layerProperties() {
			const self = this;
			return shadow(this, "_layerProperties", {
				get annotationEditorUIManager() {
					return self.#annotationEditorUIManager;
				},
				get annotationStorage() {
					return self.pdfDocument?.annotationStorage;
				},
				get downloadManager() {
					return self.downloadManager;
				},
				get enableScripting() {
					return !!self._scriptingManager;
				},
				get fieldObjectsPromise() {
					return self.pdfDocument?.getFieldObjects();
				},
				get findController() {
					return self.findController;
				},
				get hasJSActionsPromise() {
					return self.pdfDocument?.hasJSActions();
				},
				get linkService() {
					return self.linkService;
				}
			});
		}
		#initializePermissions(permissions) {
			const params = {
				annotationEditorMode: this.#annotationEditorMode,
				annotationMode: this.#annotationMode,
				textLayerMode: this.#textLayerMode
			};
			if (!permissions) return params;
			if (!permissions.includes(PermissionFlag.COPY) && this.#textLayerMode === TextLayerMode.ENABLE) params.textLayerMode = TextLayerMode.ENABLE_PERMISSIONS;
			if (!permissions.includes(PermissionFlag.MODIFY_CONTENTS)) params.annotationEditorMode = AnnotationEditorType.DISABLE;
			if (!permissions.includes(PermissionFlag.MODIFY_ANNOTATIONS) && !permissions.includes(PermissionFlag.FILL_INTERACTIVE_FORMS) && this.#annotationMode === AnnotationMode.ENABLE_FORMS) params.annotationMode = AnnotationMode.ENABLE;
			return params;
		}
		async #onePageRenderedOrForceFetch(signal) {
			if (document.visibilityState === "hidden" || !this.container.offsetParent || this._getVisiblePages().views.length === 0) return;
			const hiddenCapability = Promise.withResolvers(), ac = new AbortController();
			document.addEventListener("visibilitychange", () => {
				if (document.visibilityState === "hidden") hiddenCapability.resolve();
			}, { signal: typeof AbortSignal.any === "function" ? AbortSignal.any([signal, ac.signal]) : signal });
			await Promise.race([this._onePageRenderedCapability.promise, hiddenCapability.promise]);
			ac.abort();
		}
		async getAllText() {
			const texts = [];
			const buffer = [];
			for (let pageNum = 1, pagesCount = this.pdfDocument.numPages; pageNum <= pagesCount; ++pageNum) {
				if (this.#interruptCopyCondition) return null;
				buffer.length = 0;
				const { items } = await (await this.pdfDocument.getPage(pageNum)).getTextContent();
				for (const item of items) {
					if (item.str) buffer.push(item.str);
					if (item.hasEOL) buffer.push("\n");
				}
				texts.push(removeNullCharacters(buffer.join("")));
			}
			return texts.join("\n");
		}
		#copyCallback(textLayerMode, event) {
			const selection = document.getSelection();
			const { focusNode, anchorNode } = selection;
			if (anchorNode && focusNode && selection.containsNode(this.#hiddenCopyElement)) {
				if (this.#getAllTextInProgress || textLayerMode === TextLayerMode.ENABLE_PERMISSIONS) {
					stopEvent(event);
					return;
				}
				this.#getAllTextInProgress = true;
				const { classList } = this.viewer;
				classList.add("copyAll");
				const ac = new AbortController();
				window.addEventListener("keydown", (ev) => this.#interruptCopyCondition = ev.key === "Escape", { signal: ac.signal });
				this.getAllText().then(async (text) => {
					if (text !== null) await navigator.clipboard.writeText(text);
				}).catch((reason) => {
					console.warn(`Something goes wrong when extracting the text: ${reason.message}`);
				}).finally(() => {
					this.#getAllTextInProgress = false;
					this.#interruptCopyCondition = false;
					ac.abort();
					classList.remove("copyAll");
				});
				stopEvent(event);
			}
		}
		setDocument(pdfDocument) {
			if (this.pdfDocument) {
				this.eventBus.dispatch("pagesdestroy", { source: this });
				this._cancelRendering();
				this._resetView();
				this.findController?.setDocument(null);
				this._scriptingManager?.setDocument(null);
				this.#annotationEditorUIManager?.destroy();
				this.#annotationEditorUIManager = null;
			}
			this.pdfDocument = pdfDocument;
			if (!pdfDocument) return;
			const pagesCount = pdfDocument.numPages;
			const firstPagePromise = pdfDocument.getPage(1);
			const optionalContentConfigPromise = pdfDocument.getOptionalContentConfig({ intent: "display" });
			const permissionsPromise = this.#enablePermissions ? pdfDocument.getPermissions() : Promise.resolve();
			const { eventBus, pageColors, viewer } = this;
			this.#eventAbortController = new AbortController();
			const { signal } = this.#eventAbortController;
			if (pagesCount > PagesCountLimit.FORCE_SCROLL_MODE_PAGE) {
				console.warn("Forcing PAGE-scrolling for performance reasons, given the length of the document.");
				const mode = this._scrollMode = ScrollMode.PAGE;
				eventBus.dispatch("scrollmodechanged", {
					source: this,
					mode
				});
			}
			this._pagesCapability.promise.then(() => {
				eventBus.dispatch("pagesloaded", {
					source: this,
					pagesCount
				});
			}, () => {});
			const onBeforeDraw = (evt) => {
				const pageView = this._pages[evt.pageNumber - 1];
				if (!pageView) return;
				this.#buffer.push(pageView);
			};
			eventBus._on("pagerender", onBeforeDraw, { signal });
			const onAfterDraw = (evt) => {
				if (evt.cssTransform) return;
				this._onePageRenderedCapability.resolve({ timestamp: evt.timestamp });
				eventBus._off("pagerendered", onAfterDraw);
			};
			eventBus._on("pagerendered", onAfterDraw, { signal });
			Promise.all([firstPagePromise, permissionsPromise]).then(([firstPdfPage, permissions]) => {
				if (pdfDocument !== this.pdfDocument) return;
				this._firstPageCapability.resolve(firstPdfPage);
				this._optionalContentConfigPromise = optionalContentConfigPromise;
				const { annotationEditorMode, annotationMode, textLayerMode } = this.#initializePermissions(permissions);
				if (textLayerMode !== TextLayerMode.DISABLE) {
					const element = this.#hiddenCopyElement = document.createElement("div");
					element.id = "hiddenCopyElement";
					viewer.before(element);
				}
				if (typeof AbortSignal.any === "function" && annotationEditorMode !== AnnotationEditorType.DISABLE) {
					const mode = annotationEditorMode;
					if (pdfDocument.isPureXfa) console.warn("Warning: XFA-editing is not implemented.");
					else if (isValidAnnotationEditorMode(mode)) {
						this.#annotationEditorUIManager = new AnnotationEditorUIManager(this.container, viewer, this.#altTextManager, eventBus, pdfDocument, pageColors, this.#annotationEditorHighlightColors, this.#enableHighlightFloatingButton, this.#enableUpdatedAddImage, this.#enableNewAltTextWhenAddingImage, this.#mlManager, this.#editorUndoBar, this.#supportsPinchToZoom);
						eventBus.dispatch("annotationeditoruimanager", {
							source: this,
							uiManager: this.#annotationEditorUIManager
						});
						if (mode !== AnnotationEditorType.NONE) {
							if (mode === AnnotationEditorType.STAMP) this.#mlManager?.loadModel("altText");
							this.#annotationEditorUIManager.updateMode(mode);
						}
					} else console.error(`Invalid AnnotationEditor mode: ${mode}`);
				}
				const viewerElement = this._scrollMode === ScrollMode.PAGE ? null : viewer;
				const scale = this.currentScale;
				const viewport = firstPdfPage.getViewport({ scale: scale * PixelsPerInch.PDF_TO_CSS_UNITS });
				viewer.style.setProperty("--scale-factor", viewport.scale);
				if (pageColors?.background) viewer.style.setProperty("--page-bg-color", pageColors.background);
				if (pageColors?.foreground === "CanvasText" || pageColors?.background === "Canvas") {
					viewer.style.setProperty("--hcm-highlight-filter", pdfDocument.filterFactory.addHighlightHCMFilter("highlight", "CanvasText", "Canvas", "HighlightText", "Highlight"));
					viewer.style.setProperty("--hcm-highlight-selected-filter", pdfDocument.filterFactory.addHighlightHCMFilter("highlight_selected", "CanvasText", "Canvas", "HighlightText", "ButtonText"));
				}
				for (let pageNum = 1; pageNum <= pagesCount; ++pageNum) {
					const pageView = new PDFPageView({
						container: viewerElement,
						eventBus,
						id: pageNum,
						scale,
						defaultViewport: viewport.clone(),
						optionalContentConfigPromise,
						renderingQueue: this.renderingQueue,
						textLayerMode,
						annotationMode,
						imageResourcesPath: this.imageResourcesPath,
						maxCanvasPixels: this.maxCanvasPixels,
						pageColors,
						l10n: this.l10n,
						layerProperties: this._layerProperties,
						enableHWA: this.#enableHWA
					});
					this._pages.push(pageView);
				}
				this._pages[0]?.setPdfPage(firstPdfPage);
				if (this._scrollMode === ScrollMode.PAGE) this.#ensurePageViewVisible();
				else if (this._spreadMode !== SpreadMode.NONE) this._updateSpreadMode();
				this.#onePageRenderedOrForceFetch(signal).then(async () => {
					if (pdfDocument !== this.pdfDocument) return;
					this.findController?.setDocument(pdfDocument);
					this._scriptingManager?.setDocument(pdfDocument);
					if (this.#hiddenCopyElement) document.addEventListener("copy", this.#copyCallback.bind(this, textLayerMode), { signal });
					if (this.#annotationEditorUIManager) eventBus.dispatch("annotationeditormodechanged", {
						source: this,
						mode: this.#annotationEditorMode
					});
					if (pdfDocument.loadingParams.disableAutoFetch || pagesCount > PagesCountLimit.FORCE_LAZY_PAGE_INIT) {
						this._pagesCapability.resolve();
						return;
					}
					let getPagesLeft = pagesCount - 1;
					if (getPagesLeft <= 0) {
						this._pagesCapability.resolve();
						return;
					}
					for (let pageNum = 2; pageNum <= pagesCount; ++pageNum) {
						const promise = pdfDocument.getPage(pageNum).then((pdfPage) => {
							const pageView = this._pages[pageNum - 1];
							if (!pageView.pdfPage) pageView.setPdfPage(pdfPage);
							if (--getPagesLeft === 0) this._pagesCapability.resolve();
						}, (reason) => {
							console.error(`Unable to get page ${pageNum} to initialize viewer`, reason);
							if (--getPagesLeft === 0) this._pagesCapability.resolve();
						});
						if (pageNum % PagesCountLimit.PAUSE_EAGER_PAGE_INIT === 0) await promise;
					}
				});
				eventBus.dispatch("pagesinit", { source: this });
				pdfDocument.getMetadata().then(({ info }) => {
					if (pdfDocument !== this.pdfDocument) return;
					if (info.Language) viewer.lang = info.Language;
				});
				if (this.defaultRenderingQueue) this.update();
			}).catch((reason) => {
				console.error("Unable to initialize viewer", reason);
				this._pagesCapability.reject(reason);
			});
		}
		setPageLabels(labels) {
			if (!this.pdfDocument) return;
			if (!labels) this._pageLabels = null;
			else if (!(Array.isArray(labels) && this.pdfDocument.numPages === labels.length)) {
				this._pageLabels = null;
				console.error(`setPageLabels: Invalid page labels.`);
			} else this._pageLabels = labels;
			for (let i = 0, ii = this._pages.length; i < ii; i++) this._pages[i].setPageLabel(this._pageLabels?.[i] ?? null);
		}
		_resetView() {
			this._pages = [];
			this._currentPageNumber = 1;
			this._currentScale = UNKNOWN_SCALE;
			this._currentScaleValue = null;
			this._pageLabels = null;
			this.#buffer = new PDFPageViewBuffer(DEFAULT_CACHE_SIZE);
			this._location = null;
			this._pagesRotation = 0;
			this._optionalContentConfigPromise = null;
			this._firstPageCapability = Promise.withResolvers();
			this._onePageRenderedCapability = Promise.withResolvers();
			this._pagesCapability = Promise.withResolvers();
			this._scrollMode = ScrollMode.VERTICAL;
			this._previousScrollMode = ScrollMode.UNKNOWN;
			this._spreadMode = SpreadMode.NONE;
			this.#scrollModePageState = {
				previousPageNumber: 1,
				scrollDown: true,
				pages: []
			};
			this.#eventAbortController?.abort();
			this.#eventAbortController = null;
			this.viewer.textContent = "";
			this._updateScrollMode();
			this.viewer.removeAttribute("lang");
			this.#hiddenCopyElement?.remove();
			this.#hiddenCopyElement = null;
			this.#cleanupSwitchAnnotationEditorMode();
		}
		#ensurePageViewVisible() {
			if (this._scrollMode !== ScrollMode.PAGE) throw new Error("#ensurePageViewVisible: Invalid scrollMode value.");
			const pageNumber = this._currentPageNumber, state = this.#scrollModePageState, viewer = this.viewer;
			viewer.textContent = "";
			state.pages.length = 0;
			if (this._spreadMode === SpreadMode.NONE && !this.isInPresentationMode) {
				const pageView = this._pages[pageNumber - 1];
				viewer.append(pageView.div);
				state.pages.push(pageView);
			} else {
				const pageIndexSet = /* @__PURE__ */ new Set(), parity = this._spreadMode - 1;
				if (parity === -1) pageIndexSet.add(pageNumber - 1);
				else if (pageNumber % 2 !== parity) {
					pageIndexSet.add(pageNumber - 1);
					pageIndexSet.add(pageNumber);
				} else {
					pageIndexSet.add(pageNumber - 2);
					pageIndexSet.add(pageNumber - 1);
				}
				const spread = document.createElement("div");
				spread.className = "spread";
				if (this.isInPresentationMode) {
					const dummyPage = document.createElement("div");
					dummyPage.className = "dummyPage";
					spread.append(dummyPage);
				}
				for (const i of pageIndexSet) {
					const pageView = this._pages[i];
					if (!pageView) continue;
					spread.append(pageView.div);
					state.pages.push(pageView);
				}
				viewer.append(spread);
			}
			state.scrollDown = pageNumber >= state.previousPageNumber;
			state.previousPageNumber = pageNumber;
		}
		_scrollUpdate() {
			if (this.pagesCount === 0) return;
			this.update();
		}
		#scrollIntoView(pageView, pageSpot = null) {
			const { div, id } = pageView;
			if (this._currentPageNumber !== id) this._setCurrentPageNumber(id);
			if (this._scrollMode === ScrollMode.PAGE) {
				this.#ensurePageViewVisible();
				this.update();
			}
			if (!pageSpot && !this.isInPresentationMode) {
				const left = div.offsetLeft + div.clientLeft, right = left + div.clientWidth;
				const { scrollLeft, clientWidth } = this.container;
				if (this._scrollMode === ScrollMode.HORIZONTAL || left < scrollLeft || right > scrollLeft + clientWidth) pageSpot = {
					left: 0,
					top: 0
				};
			}
			scrollIntoView(div, pageSpot);
			if (!this._currentScaleValue && this._location) this._location = null;
		}
		#isSameScale(newScale) {
			return newScale === this._currentScale || Math.abs(newScale - this._currentScale) < 1e-15;
		}
		#setScaleUpdatePages(newScale, newValue, { noScroll = false, preset = false, drawingDelay = -1, origin = null }) {
			this._currentScaleValue = newValue.toString();
			if (this.#isSameScale(newScale)) {
				if (preset) this.eventBus.dispatch("scalechanging", {
					source: this,
					scale: newScale,
					presetValue: newValue
				});
				return;
			}
			this.viewer.style.setProperty("--scale-factor", newScale * PixelsPerInch.PDF_TO_CSS_UNITS);
			const postponeDrawing = drawingDelay >= 0 && drawingDelay < 1e3;
			this.refresh(true, {
				scale: newScale,
				drawingDelay: postponeDrawing ? drawingDelay : -1
			});
			if (postponeDrawing) this.#scaleTimeoutId = setTimeout(() => {
				this.#scaleTimeoutId = null;
				this.refresh();
			}, drawingDelay);
			const previousScale = this._currentScale;
			this._currentScale = newScale;
			if (!noScroll) {
				let page = this._currentPageNumber, dest;
				if (this._location && !(this.isInPresentationMode || this.isChangingPresentationMode)) {
					page = this._location.pageNumber;
					dest = [
						null,
						{ name: "XYZ" },
						this._location.left,
						this._location.top,
						null
					];
				}
				this.scrollPageIntoView({
					pageNumber: page,
					destArray: dest,
					allowNegativeOffset: true
				});
				if (Array.isArray(origin)) {
					const scaleDiff = newScale / previousScale - 1;
					const [top, left] = this.containerTopLeft;
					this.container.scrollLeft += (origin[0] - left) * scaleDiff;
					this.container.scrollTop += (origin[1] - top) * scaleDiff;
				}
			}
			this.eventBus.dispatch("scalechanging", {
				source: this,
				scale: newScale,
				presetValue: preset ? newValue : void 0
			});
			if (this.defaultRenderingQueue) this.update();
		}
		get #pageWidthScaleFactor() {
			if (this._spreadMode !== SpreadMode.NONE && this._scrollMode !== ScrollMode.HORIZONTAL) return 2;
			return 1;
		}
		#setScale(value, options) {
			let scale = parseFloat(value);
			if (scale > 0) {
				options.preset = false;
				this.#setScaleUpdatePages(scale, value, options);
			} else {
				const currentPage = this._pages[this._currentPageNumber - 1];
				if (!currentPage) return;
				let hPadding = SCROLLBAR_PADDING, vPadding = VERTICAL_PADDING;
				if (this.isInPresentationMode) {
					hPadding = vPadding = 4;
					if (this._spreadMode !== SpreadMode.NONE) hPadding *= 2;
				} else if (this.removePageBorders) hPadding = vPadding = 0;
				else if (this._scrollMode === ScrollMode.HORIZONTAL) [hPadding, vPadding] = [vPadding, hPadding];
				const pageWidthScale = (this.container.clientWidth - hPadding) / currentPage.width * currentPage.scale / this.#pageWidthScaleFactor;
				const pageHeightScale = (this.container.clientHeight - vPadding) / currentPage.height * currentPage.scale;
				switch (value) {
					case "page-actual":
						scale = 1;
						break;
					case "page-width":
						scale = pageWidthScale;
						break;
					case "page-height":
						scale = pageHeightScale;
						break;
					case "page-fit":
						scale = Math.min(pageWidthScale, pageHeightScale);
						break;
					case "auto":
						const horizontalScale = isPortraitOrientation(currentPage) ? pageWidthScale : Math.min(pageHeightScale, pageWidthScale);
						scale = Math.min(MAX_AUTO_SCALE, horizontalScale);
						break;
					default:
						console.error(`#setScale: "${value}" is an unknown zoom value.`);
						return;
				}
				options.preset = true;
				this.#setScaleUpdatePages(scale, value, options);
			}
		}
		#resetCurrentPageView() {
			const pageView = this._pages[this._currentPageNumber - 1];
			if (this.isInPresentationMode) this.#setScale(this._currentScaleValue, { noScroll: true });
			this.#scrollIntoView(pageView);
		}
		pageLabelToPageNumber(label) {
			if (!this._pageLabels) return null;
			const i = this._pageLabels.indexOf(label);
			if (i < 0) return null;
			return i + 1;
		}
		scrollPageIntoView({ pageNumber, destArray = null, allowNegativeOffset = false, ignoreDestinationZoom = false }) {
			if (!this.pdfDocument) return;
			const pageView = Number.isInteger(pageNumber) && this._pages[pageNumber - 1];
			if (!pageView) {
				console.error(`scrollPageIntoView: "${pageNumber}" is not a valid pageNumber parameter.`);
				return;
			}
			if (this.isInPresentationMode || !destArray) {
				this._setCurrentPageNumber(pageNumber, true);
				return;
			}
			let x = 0, y = 0;
			let width = 0, height = 0, widthScale, heightScale;
			const changeOrientation = pageView.rotation % 180 !== 0;
			const pageWidth = (changeOrientation ? pageView.height : pageView.width) / pageView.scale / PixelsPerInch.PDF_TO_CSS_UNITS;
			const pageHeight = (changeOrientation ? pageView.width : pageView.height) / pageView.scale / PixelsPerInch.PDF_TO_CSS_UNITS;
			let scale = 0;
			switch (destArray[1].name) {
				case "XYZ":
					x = destArray[2];
					y = destArray[3];
					scale = destArray[4];
					x = x !== null ? x : 0;
					y = y !== null ? y : pageHeight;
					break;
				case "Fit":
				case "FitB":
					scale = "page-fit";
					break;
				case "FitH":
				case "FitBH":
					y = destArray[2];
					scale = "page-width";
					if (y === null && this._location) {
						x = this._location.left;
						y = this._location.top;
					} else if (typeof y !== "number" || y < 0) y = pageHeight;
					break;
				case "FitV":
				case "FitBV":
					x = destArray[2];
					width = pageWidth;
					height = pageHeight;
					scale = "page-height";
					break;
				case "FitR":
					x = destArray[2];
					y = destArray[3];
					width = destArray[4] - x;
					height = destArray[5] - y;
					let hPadding = SCROLLBAR_PADDING, vPadding = VERTICAL_PADDING;
					if (this.removePageBorders) hPadding = vPadding = 0;
					widthScale = (this.container.clientWidth - hPadding) / width / PixelsPerInch.PDF_TO_CSS_UNITS;
					heightScale = (this.container.clientHeight - vPadding) / height / PixelsPerInch.PDF_TO_CSS_UNITS;
					scale = Math.min(Math.abs(widthScale), Math.abs(heightScale));
					break;
				default:
					console.error(`scrollPageIntoView: "${destArray[1].name}" is not a valid destination type.`);
					return;
			}
			if (!ignoreDestinationZoom) {
				if (scale && scale !== this._currentScale) this.currentScaleValue = scale;
				else if (this._currentScale === UNKNOWN_SCALE) this.currentScaleValue = DEFAULT_SCALE_VALUE;
			}
			if (scale === "page-fit" && !destArray[4]) {
				this.#scrollIntoView(pageView);
				return;
			}
			const boundingRect = [pageView.viewport.convertToViewportPoint(x, y), pageView.viewport.convertToViewportPoint(x + width, y + height)];
			let left = Math.min(boundingRect[0][0], boundingRect[1][0]);
			let top = Math.min(boundingRect[0][1], boundingRect[1][1]);
			if (!allowNegativeOffset) {
				left = Math.max(left, 0);
				top = Math.max(top, 0);
			}
			this.#scrollIntoView(pageView, {
				left,
				top
			});
		}
		_updateLocation(firstPage) {
			const currentScale = this._currentScale;
			const currentScaleValue = this._currentScaleValue;
			const normalizedScaleValue = parseFloat(currentScaleValue) === currentScale ? Math.round(currentScale * 1e4) / 100 : currentScaleValue;
			const pageNumber = firstPage.id;
			const currentPageView = this._pages[pageNumber - 1];
			const container = this.container;
			const topLeft = currentPageView.getPagePoint(container.scrollLeft - firstPage.x, container.scrollTop - firstPage.y);
			const intLeft = Math.round(topLeft[0]);
			const intTop = Math.round(topLeft[1]);
			let pdfOpenParams = `#page=${pageNumber}`;
			if (!this.isInPresentationMode) pdfOpenParams += `&zoom=${normalizedScaleValue},${intLeft},${intTop}`;
			this._location = {
				pageNumber,
				scale: normalizedScaleValue,
				top: intTop,
				left: intLeft,
				rotation: this._pagesRotation,
				pdfOpenParams
			};
		}
		update() {
			const visible = this._getVisiblePages();
			const visiblePages = visible.views, numVisiblePages = visiblePages.length;
			if (numVisiblePages === 0) return;
			const newCacheSize = Math.max(DEFAULT_CACHE_SIZE, 2 * numVisiblePages + 1);
			this.#buffer.resize(newCacheSize, visible.ids);
			this.renderingQueue.renderHighestPriority(visible);
			const isSimpleLayout = this._spreadMode === SpreadMode.NONE && (this._scrollMode === ScrollMode.PAGE || this._scrollMode === ScrollMode.VERTICAL);
			const currentId = this._currentPageNumber;
			let stillFullyVisible = false;
			for (const page of visiblePages) {
				if (page.percent < 100) break;
				if (page.id === currentId && isSimpleLayout) {
					stillFullyVisible = true;
					break;
				}
			}
			this._setCurrentPageNumber(stillFullyVisible ? currentId : visiblePages[0].id);
			this._updateLocation(visible.first);
			this.eventBus.dispatch("updateviewarea", {
				source: this,
				location: this._location
			});
		}
		#switchToEditAnnotationMode() {
			const visible = this._getVisiblePages();
			const pagesToRefresh = [];
			const { ids, views } = visible;
			for (const page of views) {
				const { view } = page;
				if (!view.hasEditableAnnotations()) {
					ids.delete(view.id);
					continue;
				}
				pagesToRefresh.push(page);
			}
			if (pagesToRefresh.length === 0) return null;
			this.renderingQueue.renderHighestPriority({
				first: pagesToRefresh[0],
				last: pagesToRefresh.at(-1),
				views: pagesToRefresh,
				ids
			});
			return ids;
		}
		containsElement(element) {
			return this.container.contains(element);
		}
		focus() {
			this.container.focus();
		}
		get _isContainerRtl() {
			return getComputedStyle(this.container).direction === "rtl";
		}
		get isInPresentationMode() {
			return this.presentationModeState === PresentationModeState.FULLSCREEN;
		}
		get isChangingPresentationMode() {
			return this.presentationModeState === PresentationModeState.CHANGING;
		}
		get isHorizontalScrollbarEnabled() {
			return this.isInPresentationMode ? false : this.container.scrollWidth > this.container.clientWidth;
		}
		get isVerticalScrollbarEnabled() {
			return this.isInPresentationMode ? false : this.container.scrollHeight > this.container.clientHeight;
		}
		_getVisiblePages() {
			const views = this._scrollMode === ScrollMode.PAGE ? this.#scrollModePageState.pages : this._pages, horizontal = this._scrollMode === ScrollMode.HORIZONTAL, rtl = horizontal && this._isContainerRtl;
			return getVisibleElements({
				scrollEl: this.container,
				views,
				sortByVisibility: true,
				horizontal,
				rtl
			});
		}
		cleanup() {
			for (const pageView of this._pages) if (pageView.renderingState !== RenderingStates.FINISHED) pageView.reset();
		}
		_cancelRendering() {
			for (const pageView of this._pages) pageView.cancelRendering();
		}
		async #ensurePdfPageLoaded(pageView) {
			if (pageView.pdfPage) return pageView.pdfPage;
			try {
				const pdfPage = await this.pdfDocument.getPage(pageView.id);
				if (!pageView.pdfPage) pageView.setPdfPage(pdfPage);
				return pdfPage;
			} catch (reason) {
				console.error("Unable to get page for page view", reason);
				return null;
			}
		}
		#getScrollAhead(visible) {
			if (visible.first?.id === 1) return true;
			else if (visible.last?.id === this.pagesCount) return false;
			switch (this._scrollMode) {
				case ScrollMode.PAGE: return this.#scrollModePageState.scrollDown;
				case ScrollMode.HORIZONTAL: return this.scroll.right;
			}
			return this.scroll.down;
		}
		forceRendering(currentlyVisiblePages) {
			const visiblePages = currentlyVisiblePages || this._getVisiblePages();
			const scrollAhead = this.#getScrollAhead(visiblePages);
			const preRenderExtra = this._spreadMode !== SpreadMode.NONE && this._scrollMode !== ScrollMode.HORIZONTAL;
			const pageView = this.renderingQueue.getHighestPriority(visiblePages, this._pages, scrollAhead, preRenderExtra);
			if (pageView) {
				this.#ensurePdfPageLoaded(pageView).then(() => {
					this.renderingQueue.renderView(pageView);
				});
				return true;
			}
			return false;
		}
		get hasEqualPageSizes() {
			const firstPageView = this._pages[0];
			for (let i = 1, ii = this._pages.length; i < ii; ++i) {
				const pageView = this._pages[i];
				if (pageView.width !== firstPageView.width || pageView.height !== firstPageView.height) return false;
			}
			return true;
		}
		getPagesOverview() {
			let initialOrientation;
			return this._pages.map((pageView) => {
				const viewport = pageView.pdfPage.getViewport({ scale: 1 });
				const orientation = isPortraitOrientation(viewport);
				if (initialOrientation === void 0) initialOrientation = orientation;
				else if (this.enablePrintAutoRotate && orientation !== initialOrientation) return {
					width: viewport.height,
					height: viewport.width,
					rotation: (viewport.rotation - 90) % 360
				};
				return {
					width: viewport.width,
					height: viewport.height,
					rotation: viewport.rotation
				};
			});
		}
		get optionalContentConfigPromise() {
			if (!this.pdfDocument) return Promise.resolve(null);
			if (!this._optionalContentConfigPromise) {
				console.error("optionalContentConfigPromise: Not initialized yet.");
				return this.pdfDocument.getOptionalContentConfig({ intent: "display" });
			}
			return this._optionalContentConfigPromise;
		}
		set optionalContentConfigPromise(promise) {
			if (!(promise instanceof Promise)) throw new Error(`Invalid optionalContentConfigPromise: ${promise}`);
			if (!this.pdfDocument) return;
			if (!this._optionalContentConfigPromise) return;
			this._optionalContentConfigPromise = promise;
			this.refresh(false, { optionalContentConfigPromise: promise });
			this.eventBus.dispatch("optionalcontentconfigchanged", {
				source: this,
				promise
			});
		}
		get scrollMode() {
			return this._scrollMode;
		}
		set scrollMode(mode) {
			if (this._scrollMode === mode) return;
			if (!isValidScrollMode(mode)) throw new Error(`Invalid scroll mode: ${mode}`);
			if (this.pagesCount > PagesCountLimit.FORCE_SCROLL_MODE_PAGE) return;
			this._previousScrollMode = this._scrollMode;
			this._scrollMode = mode;
			this.eventBus.dispatch("scrollmodechanged", {
				source: this,
				mode
			});
			this._updateScrollMode(this._currentPageNumber);
		}
		_updateScrollMode(pageNumber = null) {
			const scrollMode = this._scrollMode, viewer = this.viewer;
			viewer.classList.toggle("scrollHorizontal", scrollMode === ScrollMode.HORIZONTAL);
			viewer.classList.toggle("scrollWrapped", scrollMode === ScrollMode.WRAPPED);
			if (!this.pdfDocument || !pageNumber) return;
			if (scrollMode === ScrollMode.PAGE) this.#ensurePageViewVisible();
			else if (this._previousScrollMode === ScrollMode.PAGE) this._updateSpreadMode();
			if (this._currentScaleValue && isNaN(this._currentScaleValue)) this.#setScale(this._currentScaleValue, { noScroll: true });
			this._setCurrentPageNumber(pageNumber, true);
			this.update();
		}
		get spreadMode() {
			return this._spreadMode;
		}
		set spreadMode(mode) {
			if (this._spreadMode === mode) return;
			if (!isValidSpreadMode(mode)) throw new Error(`Invalid spread mode: ${mode}`);
			this._spreadMode = mode;
			this.eventBus.dispatch("spreadmodechanged", {
				source: this,
				mode
			});
			this._updateSpreadMode(this._currentPageNumber);
		}
		_updateSpreadMode(pageNumber = null) {
			if (!this.pdfDocument) return;
			const viewer = this.viewer, pages = this._pages;
			if (this._scrollMode === ScrollMode.PAGE) this.#ensurePageViewVisible();
			else {
				viewer.textContent = "";
				if (this._spreadMode === SpreadMode.NONE) for (const pageView of this._pages) viewer.append(pageView.div);
				else {
					const parity = this._spreadMode - 1;
					let spread = null;
					for (let i = 0, ii = pages.length; i < ii; ++i) {
						if (spread === null) {
							spread = document.createElement("div");
							spread.className = "spread";
							viewer.append(spread);
						} else if (i % 2 === parity) {
							spread = spread.cloneNode(false);
							viewer.append(spread);
						}
						spread.append(pages[i].div);
					}
				}
			}
			if (!pageNumber) return;
			if (this._currentScaleValue && isNaN(this._currentScaleValue)) this.#setScale(this._currentScaleValue, { noScroll: true });
			this._setCurrentPageNumber(pageNumber, true);
			this.update();
		}
		_getPageAdvance(currentPageNumber, previous = false) {
			switch (this._scrollMode) {
				case ScrollMode.WRAPPED: {
					const { views } = this._getVisiblePages(), pageLayout = /* @__PURE__ */ new Map();
					for (const { id, y, percent, widthPercent } of views) {
						if (percent === 0 || widthPercent < 100) continue;
						let yArray = pageLayout.get(y);
						if (!yArray) pageLayout.set(y, yArray ||= []);
						yArray.push(id);
					}
					for (const yArray of pageLayout.values()) {
						const currentIndex = yArray.indexOf(currentPageNumber);
						if (currentIndex === -1) continue;
						const numPages = yArray.length;
						if (numPages === 1) break;
						if (previous) for (let i = currentIndex - 1, ii = 0; i >= ii; i--) {
							const currentId = yArray[i], expectedId = yArray[i + 1] - 1;
							if (currentId < expectedId) return currentPageNumber - expectedId;
						}
						else for (let i = currentIndex + 1, ii = numPages; i < ii; i++) {
							const currentId = yArray[i], expectedId = yArray[i - 1] + 1;
							if (currentId > expectedId) return expectedId - currentPageNumber;
						}
						if (previous) {
							const firstId = yArray[0];
							if (firstId < currentPageNumber) return currentPageNumber - firstId + 1;
						} else {
							const lastId = yArray[numPages - 1];
							if (lastId > currentPageNumber) return lastId - currentPageNumber + 1;
						}
						break;
					}
					break;
				}
				case ScrollMode.HORIZONTAL: break;
				case ScrollMode.PAGE:
				case ScrollMode.VERTICAL: {
					if (this._spreadMode === SpreadMode.NONE) break;
					const parity = this._spreadMode - 1;
					if (previous && currentPageNumber % 2 !== parity) break;
					else if (!previous && currentPageNumber % 2 === parity) break;
					const { views } = this._getVisiblePages(), expectedId = previous ? currentPageNumber - 1 : currentPageNumber + 1;
					for (const { id, percent, widthPercent } of views) {
						if (id !== expectedId) continue;
						if (percent > 0 && widthPercent === 100) return 2;
						break;
					}
					break;
				}
			}
			return 1;
		}
		nextPage() {
			const currentPageNumber = this._currentPageNumber, pagesCount = this.pagesCount;
			if (currentPageNumber >= pagesCount) return false;
			const advance = this._getPageAdvance(currentPageNumber, false) || 1;
			this.currentPageNumber = Math.min(currentPageNumber + advance, pagesCount);
			return true;
		}
		previousPage() {
			const currentPageNumber = this._currentPageNumber;
			if (currentPageNumber <= 1) return false;
			const advance = this._getPageAdvance(currentPageNumber, true) || 1;
			this.currentPageNumber = Math.max(currentPageNumber - advance, 1);
			return true;
		}
		updateScale({ drawingDelay, scaleFactor = null, steps = null, origin }) {
			if (steps === null && scaleFactor === null) throw new Error("Invalid updateScale options: either `steps` or `scaleFactor` must be provided.");
			if (!this.pdfDocument) return;
			let newScale = this._currentScale;
			if (scaleFactor > 0 && scaleFactor !== 1) newScale = Math.round(newScale * scaleFactor * 100) / 100;
			else if (steps) {
				const delta = steps > 0 ? DEFAULT_SCALE_DELTA : 1 / DEFAULT_SCALE_DELTA;
				const round = steps > 0 ? Math.ceil : Math.floor;
				steps = Math.abs(steps);
				do
					newScale = round((newScale * delta).toFixed(2) * 10) / 10;
				while (--steps > 0);
			}
			newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, newScale));
			this.#setScale(newScale, {
				noScroll: false,
				drawingDelay,
				origin
			});
		}
		increaseScale(options = {}) {
			this.updateScale({
				...options,
				steps: options.steps ?? 1
			});
		}
		decreaseScale(options = {}) {
			this.updateScale({
				...options,
				steps: -(options.steps ?? 1)
			});
		}
		#updateContainerHeightCss(height = this.container.clientHeight) {
			if (height !== this.#previousContainerHeight) {
				this.#previousContainerHeight = height;
				docStyle.setProperty("--viewer-container-height", `${height}px`);
			}
		}
		#resizeObserverCallback(entries) {
			for (const entry of entries) if (entry.target === this.container) {
				this.#updateContainerHeightCss(Math.floor(entry.borderBoxSize[0].blockSize));
				this.#containerTopLeft = null;
				break;
			}
		}
		get containerTopLeft() {
			return this.#containerTopLeft ||= [this.container.offsetTop, this.container.offsetLeft];
		}
		#cleanupSwitchAnnotationEditorMode() {
			this.#switchAnnotationEditorModeAC?.abort();
			this.#switchAnnotationEditorModeAC = null;
			if (this.#switchAnnotationEditorModeTimeoutId !== null) {
				clearTimeout(this.#switchAnnotationEditorModeTimeoutId);
				this.#switchAnnotationEditorModeTimeoutId = null;
			}
		}
		get annotationEditorMode() {
			return this.#annotationEditorUIManager ? this.#annotationEditorMode : AnnotationEditorType.DISABLE;
		}
		set annotationEditorMode({ mode, editId = null, isFromKeyboard = false }) {
			if (!this.#annotationEditorUIManager) throw new Error(`The AnnotationEditor is not enabled.`);
			if (this.#annotationEditorMode === mode) return;
			if (!isValidAnnotationEditorMode(mode)) throw new Error(`Invalid AnnotationEditor mode: ${mode}`);
			if (!this.pdfDocument) return;
			if (mode === AnnotationEditorType.STAMP) this.#mlManager?.loadModel("altText");
			const { eventBus } = this;
			const updater = () => {
				this.#cleanupSwitchAnnotationEditorMode();
				this.#annotationEditorMode = mode;
				this.#annotationEditorUIManager.updateMode(mode, editId, isFromKeyboard);
				eventBus.dispatch("annotationeditormodechanged", {
					source: this,
					mode
				});
			};
			if (mode === AnnotationEditorType.NONE || this.#annotationEditorMode === AnnotationEditorType.NONE) {
				const isEditing = mode !== AnnotationEditorType.NONE;
				if (!isEditing) this.pdfDocument.annotationStorage.resetModifiedIds();
				for (const pageView of this._pages) pageView.toggleEditingMode(isEditing);
				const idsToRefresh = this.#switchToEditAnnotationMode();
				if (isEditing && idsToRefresh) {
					this.#cleanupSwitchAnnotationEditorMode();
					this.#switchAnnotationEditorModeAC = new AbortController();
					const signal = AbortSignal.any([this.#eventAbortController.signal, this.#switchAnnotationEditorModeAC.signal]);
					eventBus._on("pagerendered", ({ pageNumber }) => {
						idsToRefresh.delete(pageNumber);
						if (idsToRefresh.size === 0) this.#switchAnnotationEditorModeTimeoutId = setTimeout(updater, 0);
					}, { signal });
					return;
				}
			}
			updater();
		}
		refresh(noUpdate = false, updateArgs = Object.create(null)) {
			if (!this.pdfDocument) return;
			for (const pageView of this._pages) pageView.update(updateArgs);
			if (this.#scaleTimeoutId !== null) {
				clearTimeout(this.#scaleTimeoutId);
				this.#scaleTimeoutId = null;
			}
			if (!noUpdate) this.update();
		}
	};
	PDFSinglePageViewer = class extends PDFViewer$1 {
		_resetView() {
			super._resetView();
			this._scrollMode = ScrollMode.PAGE;
			this._spreadMode = SpreadMode.NONE;
		}
		set scrollMode(mode) {}
		_updateScrollMode() {}
		set spreadMode(mode) {}
		_updateSpreadMode() {}
	};
	__webpack_exports__AnnotationLayerBuilder = __webpack_exports__.AnnotationLayerBuilder;
	__webpack_exports__DownloadManager = __webpack_exports__.DownloadManager;
	__webpack_exports__EventBus = __webpack_exports__.EventBus;
	__webpack_exports__FindState = __webpack_exports__.FindState;
	__webpack_exports__GenericL10n = __webpack_exports__.GenericL10n;
	__webpack_exports__LinkTarget = __webpack_exports__.LinkTarget;
	__webpack_exports__PDFFindController = __webpack_exports__.PDFFindController;
	__webpack_exports__PDFHistory = __webpack_exports__.PDFHistory;
	__webpack_exports__PDFLinkService = __webpack_exports__.PDFLinkService;
	__webpack_exports__PDFPageView = __webpack_exports__.PDFPageView;
	__webpack_exports__PDFScriptingManager = __webpack_exports__.PDFScriptingManager;
	__webpack_exports__PDFSinglePageViewer = __webpack_exports__.PDFSinglePageViewer;
	__webpack_exports__PDFViewer = __webpack_exports__.PDFViewer;
	__webpack_exports__ProgressBar = __webpack_exports__.ProgressBar;
	__webpack_exports__RenderingStates = __webpack_exports__.RenderingStates;
	__webpack_exports__ScrollMode = __webpack_exports__.ScrollMode;
	__webpack_exports__SimpleLinkService = __webpack_exports__.SimpleLinkService;
	__webpack_exports__SpreadMode = __webpack_exports__.SpreadMode;
	__webpack_exports__StructTreeLayerBuilder = __webpack_exports__.StructTreeLayerBuilder;
	__webpack_exports__TextLayerBuilder = __webpack_exports__.TextLayerBuilder;
	__webpack_exports__XfaLayerBuilder = __webpack_exports__.XfaLayerBuilder;
	__webpack_exports__parseQueryString = __webpack_exports__.parseQueryString;
}));
globalThis.pdfjsLib = pdf_exports;
var pdfjsViewer = await Promise.resolve().then(() => (init_pdf_viewer_export(), pdf_viewer_export_exports));
var { getDocument, GlobalWorkerOptions, version } = pdf_exports;
var { EventBus, PDFFindController, PDFLinkService, PDFRenderingQueue, PDFViewer } = pdfjsViewer;
//#endregion
//#region hermes-plugin/plugins/themis/desktop/plugin.js
function caseSynthesisDisplayMarkdown(content) {
	const text = String(content || "");
	if (!text.trim() || /\n\s*\n/.test(text) || /^\s{0,3}#{1,6}\s/m.test(text)) return text;
	const segmenter = typeof Intl !== "undefined" && typeof Intl.Segmenter === "function" ? new Intl.Segmenter("pt-BR", { granularity: "sentence" }) : null;
	const sentences = segmenter ? Array.from(segmenter.segment(text), (item) => item.segment.trim()).filter(Boolean) : text.split(/(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])/u).map((item) => item.trim()).filter(Boolean);
	if (sentences.length < 2 && text.length <= 600) return text;
	const paragraphs = [];
	let paragraph = "";
	const addWords = (value) => {
		const words = value.split(/\s+/).filter(Boolean);
		let chunk = "";
		for (const word of words) {
			if (chunk && chunk.length + word.length + 1 > 380) {
				paragraphs.push(chunk);
				chunk = "";
			}
			chunk = chunk ? `${chunk} ${word}` : word;
		}
		return chunk;
	};
	for (const sentence of sentences) {
		if (sentence.length > 700) {
			if (paragraph) paragraphs.push(paragraph);
			paragraph = addWords(sentence);
			if (paragraph) paragraphs.push(paragraph);
			paragraph = "";
			continue;
		}
		if (paragraph && paragraph.length + sentence.length + 1 > 380) {
			paragraphs.push(paragraph);
			paragraph = sentence;
		} else paragraph = paragraph ? `${paragraph} ${sentence}` : sentence;
	}
	if (paragraph) paragraphs.push(paragraph);
	return paragraphs.length > 1 ? paragraphs.join("\n\n") : text;
}
function movementAnalysisJobFromStatus(payload) {
	const job = payload?.job;
	return job && typeof job === "object" && movementAnalysisJobIsActive(job) ? job : null;
}
function movementAnalysisJobIsActive(job) {
	return ["PENDING", "RUNNING"].includes(String(job?.status || "").toUpperCase());
}
function movementAnalysisJobForStatusUpdate(previous, processId, payload, busyProcessId) {
	const activeJob = movementAnalysisJobFromStatus(payload);
	if (activeJob) return activeJob;
	const persistedJob = payload?.job;
	if (previous?.process_id === processId && previous.job_id && previous.job_id === persistedJob?.job_id) return previous;
	if (busyProcessId === processId && movementAnalysisJobIsActive(previous)) return previous;
	return null;
}
function movementAnalysisJobMessage(job) {
	const status = String(job?.status || "").toUpperCase();
	const total = job?.total_eligible ?? job?.total ?? 0;
	if (status === "PENDING") return "Geração de resumos iniciada; aguardando execução.";
	if (status === "RUNNING") {
		const batch = job.current_batch ? ` · lote ${job.current_batch.number}/${job.batch_count || "?"} (${job.current_batch.size} Movements)` : "";
		const waiting = job.current_batch && Number(job.completed || 0) === 0 ? " · aguardando resposta do modelo" : "";
		const updated = job.updated_at ? new Date(job.updated_at).toLocaleTimeString() : "agora";
		return `Gerando resumos: ${job.completed || 0}/${total} concluídos · ${job.pending || 0} pendentes${batch}${waiting} · atualizado ${updated}`;
	}
	if (status === "COMPLETED") return `Geração de resumos concluída: ${job.completed || 0}/${total}.`;
	if (status === "PARTIAL") return `Geração de resumos parcial: ${job.completed || 0} concluídos; ${job.pending || 0} pendentes. ${job.error || ""}`;
	if (status === "FAILED") return `Geração de resumos falhou; ${job.pending ?? total} pendentes. ${job.error || ""}`;
	return "";
}
function processSelectionMatches(selection, processId, epoch) {
	return selection.pid === processId && selection.epoch === epoch;
}
function formatDateKey(isoString) {
	if (!isoString) return "";
	return String(isoString).slice(0, 10);
}
function formatDateDisplay(isoString) {
	if (!isoString) return "Data não informada";
	const dateStr = String(isoString).slice(0, 10);
	const parts = dateStr.split("-");
	if (parts.length === 3) {
		const [y, m, d] = parts;
		return `${d}/${m}/${y}`;
	}
	return dateStr;
}
function formatTimeDisplay(isoString, precision) {
	if (!isoString) return "";
	const str = String(isoString);
	if (!str.includes("T")) return "";
	const timePart = str.split("T")[1]?.slice(0, 5);
	if (!timePart) return "";
	if (timePart === "00:00" && precision !== "EXACT") return "";
	return timePart;
}
var DOCUMENT_TYPE_LABELS = {
	PETICAO_INICIAL: "Petição inicial",
	PETICAO_PROTOCOLADA: "Petição protocolada",
	"ATO ORDINATÓRIO": "Ato ordinatório",
	"CIÊNCIA DA INTIMAÇÃO": "Ciência da intimação",
	"CARTA DE CITAÇÃO": "Carta de citação",
	"SOLICITAÇÃO DE PERÍCIA MÉDICA": "Solicitação de perícia médica",
	CERTIDÃO: "Certidão",
	DECISÃO: "Decisão",
	DESPACHO: "Despacho",
	SENTENÇA: "Sentença",
	ACÓRDÃO: "Acórdão"
};
var DISPLAY_TOKEN_CASE = {
	TJSP: "TJSP",
	STJ: "STJ",
	DJEN: "DJEN",
	PJE: "PJe",
	"E-SAJ": "e-SAJ",
	"OAB/SP": "OAB/SP"
};
var PORTUGUESE_NAME_PARTICLES = /* @__PURE__ */ new Set([
	"da",
	"de",
	"do",
	"das",
	"dos",
	"e"
]);
function displayToken(token, { lowerParticles = false } = {}) {
	const uppercase = token.toLocaleUpperCase("pt-BR");
	if (DISPLAY_TOKEN_CASE[uppercase]) return DISPLAY_TOKEN_CASE[uppercase];
	const lower = token.toLocaleLowerCase("pt-BR");
	if (lowerParticles && PORTUGUESE_NAME_PARTICLES.has(lower)) return lower;
	if (token !== uppercase && token !== lower) return token;
	return lower.charAt(0).toLocaleUpperCase("pt-BR") + lower.slice(1);
}
function formatDocumentType(artifactType) {
	const value = String(artifactType || "").trim();
	if (!value) return null;
	if (DOCUMENT_TYPE_LABELS[value]) return DOCUMENT_TYPE_LABELS[value];
	if (value !== value.toUpperCase()) return value;
	const tokens = value.replace(/_/g, " ").split(/(\s+)/);
	let firstWord = true;
	return tokens.map((token) => {
		if (/^\s+$/.test(token)) return token;
		const displayed = displayToken(token);
		if (!firstWord && !DISPLAY_TOKEN_CASE[token.toLocaleUpperCase("pt-BR")]) return displayed.toLocaleLowerCase("pt-BR");
		firstWord = false;
		return displayed;
	}).join("");
}
function formatSignerDisplay(signer) {
	const value = String(signer || "").trim();
	if (!value) return null;
	return value.split(/(\s+)/).map((token) => {
		if (/^\s+$/.test(token)) return token;
		const match = token.match(/^(.+?)([.,;:]*)$/);
		const word = match ? match[1] : token;
		const punctuation = match ? match[2] : "";
		return `${displayToken(word, { lowerParticles: true })}${punctuation}`;
	}).join("");
}
function normalizeMovementsResponse(data) {
	if (Array.isArray(data)) return data;
	if (Array.isArray(data?.movements)) return data.movements;
	return [];
}
function movementActorText(movement) {
	const actor = movement?.actor;
	if (actor === null || actor === void 0) return null;
	return String(actor).trim() || null;
}
function movementActorNode(movement) {
	const actorText = movementActorText(movement);
	return actorText ? jsx("div", {
		className: "text-muted-foreground",
		children: actorText
	}) : null;
}
function cleanPieceTitle(rawTitle) {
	if (!rawTitle) return "";
	return String(rawTitle).replace(/\.pdf$/i, "").replace(/\s*\(\s*p[aá]gs?\.?\s*\d+(?:\s*[-–—]\s*\d+)?\s*\)/gi, "").trim();
}
function movementSummaryErrorMessage(error) {
	const raw = error?.message || String(error || "Falha desconhecida ao gerar resumo");
	const normalized = raw.toLocaleLowerCase("pt-BR");
	if (normalized.includes("capabilit") || normalized.includes("trust gate") || normalized.includes("consent") || normalized.includes("provider_override") || normalized.includes("model_override")) return "O Hermes ainda não autorizou as capabilities de modelo do Themis (capability not granted). Execute `hermes plugins capabilities themis` e conceda llm.provider_override e llm.model_override quando solicitado.";
	return raw;
}
function renderMovementItem(mov, idx, openAutosAtMovementPage, isExpanded = true, toggleExpand = null, summary = null, summaryLoading = false, summaryError = null, onGenerateSummary = null, summaryExpanded = true, toggleSummary = null, summaryDisabled = false) {
	const dateStr = mov.source_datetime || null;
	const movRef = mov.source_ref || null;
	const components = Array.isArray(mov.components) ? mov.components : [];
	const rawTitle = mov.title || mov.movement_type || "Movimento Processual";
	const displayTitle = cleanPieceTitle(rawTitle) || rawTitle;
	const movPageStart = movRef?.process_page_start ?? components[0]?.pages?.[0]?.process_page_number;
	const movPageEnd = movRef?.process_page_end ?? components[components.length - 1]?.pages?.slice(-1)[0]?.process_page_number ?? movPageStart;
	const totalPageLabel = movPageStart != null ? movPageEnd != null && Number(movPageEnd) > Number(movPageStart) ? `Páginas ${movPageStart}–${movPageEnd}` : `Página ${movPageStart}` : null;
	const componentNode = (component, componentIdx) => {
		const pages = Array.isArray(component?.pages) ? component.pages : [];
		const first = pages[0];
		const last = pages[pages.length - 1] || first;
		const pageStart = first?.process_page_number ?? first?.process_folio_label;
		const pageEnd = last?.process_page_number ?? last?.process_folio_label ?? pageStart;
		const pageLabel = pageStart != null ? pageEnd != null && Number(pageEnd) > Number(pageStart) ? `Páginas ${pageStart}–${pageEnd}` : `Página ${pageStart}` : null;
		const pieceRef = first && {
			document_id: first.document_id,
			pdf_page: first.pdf_page,
			process_folio: first.process_folio_label,
			process_page_start: first.process_page_number,
			process_page_end: last?.process_page_number
		};
		const rawCompTitle = component.title || component.artifact_type || "Peça interna";
		const displayCompTitle = cleanPieceTitle(rawCompTitle) || rawCompTitle;
		return jsxs("div", {
			className: "flex items-center justify-between gap-2 rounded border border-border/25 bg-background/30 px-2 py-1.5",
			children: [jsx("div", {
				className: "text-foreground/90 font-medium truncate",
				title: displayCompTitle,
				children: displayCompTitle
			}), pageLabel && pieceRef?.document_id && Number.isInteger(Number(pieceRef.pdf_page)) ? jsx(Button, {
				variant: "ghost",
				className: "h-5 px-1.5 text-[0.7rem] text-primary hover:text-primary/80 shrink-0",
				onClick: (e) => {
					if (e && e.stopPropagation) e.stopPropagation();
					openAutosAtMovementPage({ source_ref: pieceRef });
				},
				"aria-label": `Abrir Autos em ${pageLabel}`,
				children: pageLabel
			}) : null]
		}, component.component_id || component.provider_artifact_id || componentIdx);
	};
	return jsxs("div", {
		className: "rounded-md border border-border/40 bg-card/60 p-3 text-xs space-y-1.5 transition-colors hover:bg-accent/20",
		children: [
			jsxs("div", {
				className: "flex items-center justify-between gap-2 border-b border-border/20 pb-1.5",
				children: [components.length > 0 && toggleExpand ? jsxs(RowButton, {
					"aria-expanded": isExpanded,
					"aria-label": isExpanded ? "Recolher peças do movimento" : "Expandir peças do movimento",
					className: "flex min-w-0 flex-1 items-center gap-1.5 rounded-md px-1 text-left hover:bg-muted/50",
					onClick: () => toggleExpand(),
					children: [jsx(DisclosureCaret, {
						open: isExpanded,
						size: "0.75rem",
						className: "shrink-0 text-muted-foreground/70"
					}), jsxs("div", {
						className: "flex min-w-0 flex-wrap items-baseline gap-1.5",
						children: [jsx("span", {
							className: "font-semibold text-primary",
							children: `${mov.sequence != null ? `${mov.sequence}. ` : ""}${displayTitle}`
						}), dateStr ? jsx("span", {
							className: "text-[0.7rem] font-normal text-muted-foreground",
							children: `· ${dateStr}`
						}) : null]
					})]
				}) : jsxs("div", {
					className: "flex min-w-0 flex-1 flex-wrap items-baseline gap-1.5 px-1",
					children: [jsx("span", {
						className: "font-semibold text-primary",
						children: `${mov.sequence != null ? `${mov.sequence}. ` : ""}${displayTitle}`
					}), dateStr ? jsx("span", {
						className: "text-[0.7rem] font-normal text-muted-foreground",
						children: `· ${dateStr}`
					}) : null]
				}), totalPageLabel && movRef?.document_id && Number.isInteger(Number(movRef.pdf_page)) ? jsx(Button, {
					variant: "ghost",
					className: "h-5 px-1.5 text-[0.7rem] text-primary/90 hover:text-primary hover:bg-primary/10 rounded shrink-0",
					onClick: (e) => {
						if (e && e.stopPropagation) e.stopPropagation();
						openAutosAtMovementPage({ source_ref: movRef });
					},
					"aria-label": `Abrir Autos em ${totalPageLabel}`,
					children: totalPageLabel
				}) : null]
			}),
			movementActorNode(mov),
			isExpanded ? jsxs("div", {
				className: "space-y-1 pt-1",
				children: [
					mov.protocol ? jsx("div", {
						className: "text-muted-foreground",
						children: `Protocolo: ${mov.protocol}`
					}) : null,
					mov.description || mov.content ? jsx("div", {
						className: "text-foreground/90 leading-relaxed whitespace-pre-wrap",
						children: mov.description || mov.content
					}) : null,
					jsxs("div", {
						className: "border-l-2 border-primary/40 my-1 bg-muted/20 rounded-r",
						children: [jsx(RowButton, {
							"aria-expanded": summaryExpanded,
							className: "flex h-7 w-full items-center gap-1.5 rounded-r px-2 text-left text-[0.7rem] font-medium text-foreground/80 hover:bg-muted/50",
							onClick: () => toggleSummary?.(),
							children: [
								jsx(DisclosureCaret, {
									open: summaryExpanded,
									size: "0.75rem",
									className: "text-muted-foreground/70"
								}),
								jsx("span", { children: "Resumo" }),
								summary ? jsx("span", {
									className: "min-w-0 flex-1 truncate text-[0.65rem] font-normal text-muted-foreground/70",
									children: [
										summary.provider,
										summary.model,
										summary.generated_at
									].filter(Boolean).join(" · ")
								}) : null
							]
						}), summaryExpanded ? jsxs("div", {
							className: "space-y-1 px-2 pb-2",
							children: [
								jsx(PanelAction, {
									icon: summaryLoading ? "loading~spin" : summary ? "edit" : "sparkle",
									disabled: summaryLoading || summaryDisabled,
									onClick: (e) => {
										if (e && e.stopPropagation) e.stopPropagation();
										onGenerateSummary?.();
									},
									children: summaryLoading ? "Gerando resumo..." : summary ? "Atualizar resumo" : "Gerar resumo"
								}),
								summaryError ? jsx("div", {
									className: "text-[0.7rem] text-destructive",
									role: "alert",
									children: summaryError
								}) : null,
								summary ? jsx(MessageTextContent, {
									text: summary.summary_text || "",
									media: false
								}) : null
							]
						}) : null]
					}),
					components.length > 0 ? jsxs("div", {
						className: "space-y-1 pt-1",
						children: [jsx(PanelSectionLabel, { children: `Peças (${components.length})` }), components.map(componentNode)]
					}) : null
				]
			}) : null
		]
	}, mov.movement_id || idx);
}
function safeMarkdownHref(href) {
	const value = String(href || "").trim();
	return /^(https?:|mailto:)/i.test(value) ? value : null;
}
function coalesceAdjacentInlineElements(children) {
	const flattened = [];
	const flatten = (child) => {
		if (Array.isArray(child)) child.forEach(flatten);
		else if (child?.type === React.Fragment) flatten(child.props.children);
		else flattened.push(child);
	};
	flatten(children);
	return flattened.reduce((merged, child) => {
		const previous = merged[merged.length - 1];
		const separator = typeof previous === "string" && /^\s+$/.test(previous) ? previous : "";
		const candidate = separator ? merged[merged.length - 2] : previous;
		const sameType = child?.type === candidate?.type && (child?.type === "strong" || child?.type === "em");
		const textChildren = typeof candidate?.props?.children === "string" && typeof child?.props?.children === "string";
		if (sameType && textChildren) {
			const combined = jsx(candidate.type, {
				...candidate.props,
				children: candidate.props.children + separator + child.props.children
			}, candidate.key ?? child.key);
			if (separator) merged.splice(merged.length - 2, 2, combined);
			else merged[merged.length - 1] = combined;
		} else merged.push(child);
		return merged;
	}, []);
}
function renderMarkdownInline(value, keyPrefix = "inline", onCitationClick = null) {
	const text = String(value || "");
	const tokenPattern = /(\[([^\]]+)\]\(([^\s)]+)(?:\s+['\"][^)]*['\"])?\)|\[(?:Fonte\s*)?(\d+)\]|`([^`]+)`|\*\*([^*]+)\*\*|__([^_]+)__|\*([^*]+)\*|_([^_]+)_)/g;
	const parts = [];
	let cursor = 0;
	let match;
	const appendPart = (part) => {
		const previous = parts[parts.length - 1];
		if ((part.type === "strong" || part.type === "em") && previous?.type === part.type) {
			previous.text += part.text;
			return;
		}
		parts.push(part);
	};
	while ((match = tokenPattern.exec(text)) !== null) {
		if (match.index > cursor) appendPart({
			type: "text",
			text: text.slice(cursor, match.index)
		});
		const key = `${keyPrefix}-${match.index}`;
		if (match[2] !== void 0) {
			const href = safeMarkdownHref(match[3]);
			appendPart(href ? {
				type: "link",
				key,
				href,
				text: match[2]
			} : {
				type: "text",
				text: match[2]
			});
		} else if (match[4] !== void 0) appendPart({
			type: "citation",
			key,
			citeNum: parseInt(match[4], 10)
		});
		else if (match[5] !== void 0) appendPart({
			type: "code",
			key,
			text: match[5]
		});
		else if (match[6] !== void 0 || match[7] !== void 0) appendPart({
			type: "strong",
			key,
			text: match[6] || match[7]
		});
		else appendPart({
			type: "em",
			key,
			text: match[8] || match[9]
		});
		cursor = tokenPattern.lastIndex;
	}
	if (cursor < text.length) appendPart({
		type: "text",
		text: text.slice(cursor)
	});
	if (parts.length === 0) return text;
	return coalesceAdjacentInlineElements(parts.map((part) => {
		if (part.type === "text") return part.text;
		if (part.type === "link") return jsx("a", {
			href: part.href,
			target: "_blank",
			rel: "noreferrer noopener",
			children: part.text
		}, part.key);
		if (part.type === "citation") return jsx("button", {
			type: "button",
			className: "inline-flex items-center justify-center font-mono text-[0.72em] font-semibold text-primary bg-primary/10 hover:bg-primary/20 rounded px-1 py-0.2 mx-0.5 align-baseline cursor-pointer border border-primary/30 transition-colors shadow-2xs",
			title: `Ver citação [${part.citeNum}] nos Autos`,
			onClick: () => {
				if (typeof onCitationClick === "function") onCitationClick(part.citeNum);
				else if (typeof window !== "undefined" && window.__themisOpenCitation) window.__themisOpenCitation(part.citeNum);
			},
			children: `[${part.citeNum}]`
		}, part.key);
		return jsx(part.type, { children: part.text }, part.key);
	}));
}
function isMarkdownTableSeparator(line) {
	return /^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
}
function markdownTableCells(line) {
	return String(line || "").trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((cell) => cell.trim());
}
function MarkdownDocument({ content, onCitationClick = null }) {
	const lines = String(content || "").replace(/\r\n?/g, "\n").split("\n");
	const blocks = [];
	let index = 0;
	while (index < lines.length) {
		const line = lines[index];
		if (!line.trim()) {
			index += 1;
			continue;
		}
		if (line.match(/^\s*```([^\s]*)\s*$/)) {
			const code = [];
			index += 1;
			while (index < lines.length && !/^\s*```\s*$/.test(lines[index])) code.push(lines[index++]);
			if (index < lines.length) index += 1;
			blocks.push(jsx("pre", { children: jsx("code", { children: code.join("\n") }) }, `code-${blocks.length}`));
			continue;
		}
		const heading = line.match(/^(#{1,6})\s+(.+?)\s*#*\s*$/);
		if (heading) {
			const level = heading[1].length;
			blocks.push(jsx(`h${level}`, { children: renderMarkdownInline(heading[2], `heading-${blocks.length}`, onCitationClick) }, `heading-${blocks.length}`));
			index += 1;
			continue;
		}
		if (index + 1 < lines.length && line.includes("|") && isMarkdownTableSeparator(lines[index + 1])) {
			const headers = markdownTableCells(line);
			index += 2;
			const rows = [];
			while (index < lines.length && lines[index].trim() && lines[index].includes("|")) rows.push(markdownTableCells(lines[index++]));
			blocks.push(jsx("div", {
				className: "markdown-document__table-wrap",
				children: jsxs("table", { children: [jsx("thead", { children: jsx("tr", { children: headers.map((cell, cellIndex) => jsx("th", { children: renderMarkdownInline(cell, `th-${blocks.length}-${cellIndex}`, onCitationClick) }, cellIndex)) }) }), jsx("tbody", { children: rows.map((row, rowIndex) => jsx("tr", { children: headers.map((_, cellIndex) => jsx("td", { children: renderMarkdownInline(row[cellIndex] || "", `td-${blocks.length}-${rowIndex}-${cellIndex}`, onCitationClick) }, cellIndex)) }, rowIndex)) })] })
			}, `table-${blocks.length}`));
			continue;
		}
		if (line.match(/^\s*([-*+] |\d+[.)] )(.+)$/)) {
			const ordered = /^\s*\d+[.)] /.test(line);
			const items = [];
			while (index < lines.length) {
				const item = lines[index].match(/^\s*([-*+] |\d+[.)] )(.+)$/);
				if (!item || /^\s*\d+[.)] /.test(lines[index]) !== ordered) break;
				items.push(item[2]);
				index += 1;
			}
			const ListTag = ordered ? "ol" : "ul";
			blocks.push(jsx(ListTag, { children: items.map((item, itemIndex) => jsx("li", { children: renderMarkdownInline(item, `li-${blocks.length}-${itemIndex}`, onCitationClick) }, itemIndex)) }, `list-${blocks.length}`));
			continue;
		}
		if (/^\s*>\s?/.test(line)) {
			const quote = [];
			while (index < lines.length && /^\s*>\s?/.test(lines[index])) quote.push(lines[index++].replace(/^\s*>\s?/, ""));
			blocks.push(jsx("blockquote", { children: jsx(MarkdownDocument, {
				content: quote.join("\n"),
				onCitationClick
			}) }, `quote-${blocks.length}`));
			continue;
		}
		const paragraph = [line];
		index += 1;
		while (index < lines.length && lines[index].trim() && !/^\s*```/.test(lines[index]) && !/^(#{1,6})\s+/.test(lines[index]) && !/^\s*([-*+] |\d+[.)] |>\s?)/.test(lines[index]) && !(index + 1 < lines.length && lines[index].includes("|") && isMarkdownTableSeparator(lines[index + 1]))) paragraph.push(lines[index++]);
		blocks.push(jsx("p", { children: renderMarkdownInline(paragraph.join("\n"), `p-${blocks.length}`, onCitationClick) }, `p-${blocks.length}`));
	}
	return jsx("div", {
		className: "markdown-document",
		children: blocks
	});
}
var AutosPageItem = React.memo(function AutosPageItem({ page, idx, onOpenPdfInside, registerPageRef }) {
	const pageKey = sourcePageKey(page);
	const officialFolio = (page.source_ref || {}).process_folio;
	const folioMarker = officialFolio !== null && officialFolio !== void 0 ? `— ${officialFolio} —` : "—";
	const documentContext = page.document_context || {};
	const pieceContext = documentContext.piece_context || null;
	const artifactContext = documentContext.artifact_context || null;
	const submissionContext = documentContext.submission_context || null;
	const contextLine = [
		formatDocumentType(pieceContext?.piece_type || submissionContext?.submission_type || artifactContext?.artifact_type),
		formatSignerDisplay(artifactContext?.actor),
		artifactContext?.datetime || artifactContext?.event_time
	].filter(Boolean).join(" · ");
	return jsxs("article", {
		ref: (element) => registerPageRef(pageKey, element),
		className: "space-y-3.5 pt-1",
		children: [
			idx > 0 ? jsx("hr", { className: "border-0 border-t border-border/35 my-5" }) : null,
			jsx("div", {
				className: "flex min-w-0 items-center justify-between text-[0.8125rem] font-normal text-muted-foreground/70 select-none",
				children: [jsx("button", {
					type: "button",
					onClick: () => onOpenPdfInside(page),
					className: "min-w-0 font-mono font-semibold tracking-wider text-primary/80 hover:text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring transition-colors cursor-pointer",
					"aria-label": "Abrir PDF",
					children: folioMarker
				}), contextLine ? jsx("span", {
					className: "ml-2 min-w-0 truncate text-[0.78rem] text-muted-foreground/65",
					children: contextLine
				}) : null]
			}),
			page.content ? jsx("div", {
				className: "themis-document px-1 pt-0.5",
				children: jsx(MarkdownDocument, { content: page.content })
			}) : jsx("div", {
				className: "py-2 px-1 text-xs italic text-muted-foreground/50 text-center",
				children: "[Página sem conteúdo textual legível]"
			})
		]
	});
});
function deadlineUrgency(dateKey) {
	if (!/^\d{4}-\d{2}-\d{2}$/.test(String(dateKey || ""))) return { level: "normal", className: "" };
	const [year, month, day] = dateKey.split("-").map(Number);
	const due = new Date(year, month - 1, day);
	const now = new Date();
	const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
	const days = Math.round((due.getTime() - today.getTime()) / 86400000);
	if (days < 0) return { level: "past", className: "" };
	if (days === 0) return { level: "today", className: "text-red-400" };
	if (days < 3) return { level: "near", className: "text-orange-400" };
	return { level: "open", className: "text-yellow-400" };
}
function adaptLegalEventToUI(evt) {
	const kind = (evt.kind || "").toUpperCase();
	const relevantAt = evt.relevant_at || evt.due_at || evt.scheduled_at || evt.date || "";
	const dateKey = formatDateKey(relevantAt);
	const dataExibicao = formatDateDisplay(relevantAt);
	const horario = formatTimeDisplay(relevantAt, evt.date_precision);
	const processo = evt.process_id || (evt.owner_type === "PROCESS" ? evt.owner_id : "") || "";
	let tipo = "evento";
	let tipoLabel = "Evento";
	let tone = "muted";
	let codicon = "circle-outline";
	let dotClass = "bg-blue-500/70";
	let titulo = evt.title || "Evento Processual";
	let status = evt.status || "";
	let teor = evt.description || evt.outcome_notes || "Sem descrição cadastrada.";
	const meta = [];
	let providencias = "";
	let urgencyClass = "";
	let urgencyLevel = "normal";
	if (processo) meta.push({
		label: "Processo",
		value: processo
	});
	if (kind === "DEADLINE") {
		tipo = "prazo";
		tipoLabel = "Prazo";
		const urgency = deadlineUrgency(dateKey);
		urgencyClass = urgency.className;
		urgencyLevel = urgency.level;
		tone = urgency.level === "today" ? "bad" : urgency.level === "near" || urgency.level === "open" ? "warn" : "muted";
		codicon = "clock";
		dotClass = urgency.level === "today" ? "bg-red-500/70" : urgency.level === "near" ? "bg-orange-500/70" : urgency.level === "open" ? "bg-yellow-500/70" : "bg-muted-foreground/40";
		status = evt.status === "ABERTO" ? "Em aberto" : evt.status || "Calculado";
		teor = evt.determination || evt.description || "Sem determinação cadastrada.";
		if (evt.deadline_type_label) meta.push({ label: "Natureza", value: evt.deadline_type_label });
		if (evt.origin_label) meta.push({ label: "Origem do prazo", value: evt.origin_label, action: evt.origin_publication_id ? "publication" : null, target: evt.origin_publication_id || null });
		if (evt.origin_act_date_label) meta.push({ label: "Ato judicial", value: "Despacho de " + evt.origin_act_date_label + (evt.origin_folio ? " — fl. " + evt.origin_folio : ""), action: evt.origin_autos_target ? "autos" : null, target: evt.origin_autos_target || null });
		if (evt.published_on_label) meta.push({ label: "Publicação", value: evt.published_on_label, action: evt.origin_publication_id ? "publication" : null, target: evt.origin_publication_id || null });
		if (evt.counting_start_label) meta.push({ label: "Início da contagem", value: evt.counting_start_label });
		if (evt.term_label) meta.push({ label: "Prazo", value: evt.term_label });
		if (evt.due_date_label || relevantAt) meta.push({ label: "Vencimento", value: evt.due_date_label || dataExibicao });
		if (evt.counted_days_label) meta.push({ label: "Dias contados", value: evt.counted_days_label });
		if (evt.excluded_days_label) meta.push({ label: "Dias não contados", value: evt.excluded_days_label });
		if (evt.legal_basis_label) meta.push({ label: "Fundamento", value: evt.legal_basis_label });
		if (evt.responsible) meta.push({ label: "Responsável", value: evt.responsible });
		providencias = "";
	} else if (kind === "HEARING") {
		tipo = "audiencia";
		tipoLabel = "Audiência";
		tone = "warn";
		codicon = "organization";
		dotClass = "bg-amber-500/70";
		status = evt.status || "Designada";
		if (evt.hearing_type) meta.push({
			label: "Modalidade / Tipo",
			value: evt.hearing_type
		});
		if (relevantAt) meta.push({
			label: "Data / Hora",
			value: `${dataExibicao}${horario ? " às " + horario : ""}`
		});
		if (evt.location) meta.push({
			label: "Local",
			value: evt.location
		});
		if (evt.meeting_info) meta.push({
			label: "Link / Acesso",
			value: evt.meeting_info
		});
		if (Array.isArray(evt.participants) && evt.participants.length > 0) meta.push({
			label: "Participantes",
			value: evt.participants.map((p) => `${p.name}${p.role ? " (" + p.role + ")" : ""}`).join(", ")
		});
		if (evt.status) meta.push({
			label: "Status",
			value: evt.status
		});
		providencias = evt.meeting_info ? "Verificar link de acesso e documentação com antecedência." : "";
	} else if (kind === "PENDING") {
		tipo = "pendencia";
		tipoLabel = "Pendência";
		tone = "warn";
		codicon = "checklist";
		dotClass = "bg-amber-500/70";
		status = evt.status || "Pendente";
		if (evt.priority) meta.push({
			label: "Prioridade",
			value: evt.priority
		});
		if (relevantAt) meta.push({
			label: "Prazo Limite",
			value: `${dataExibicao}${horario ? " às " + horario : ""}`
		});
		if (evt.responsible) meta.push({
			label: "Responsável",
			value: evt.responsible
		});
		if (evt.source_origin) meta.push({
			label: "Origem",
			value: evt.source_origin
		});
		if (evt.status) meta.push({
			label: "Status",
			value: evt.status
		});
		providencias = evt.responsible ? `Atribuído a ${evt.responsible}. Providenciar saneamento da pendência.` : "";
	} else if (kind === "PUBLICATION") {
		tipo = "publicacao";
		tipoLabel = "Publicação";
		tone = evt.active === false || evt.canceled_on ? "bad" : "muted";
		codicon = "megaphone";
		dotClass = evt.active === false || evt.canceled_on ? "bg-red-500/70" : "bg-blue-500/70";
		status = evt.status || (evt.active === false ? "Inativa" : "DJEN");
		if (relevantAt) meta.push({
			label: evt.date_basis === "AVAILABLE" ? "Disponibilização DJEN" : "Data Publicação",
			value: `${dataExibicao}${horario ? " às " + horario : ""}`
		});
		if (evt.tribunal) meta.push({
			label: "Tribunal",
			value: evt.tribunal
		});
		if (evt.organ) meta.push({
			label: "Órgão",
			value: evt.organ
		});
		if (Array.isArray(evt.recipients) && evt.recipients.length > 0) meta.push({
			label: "Destinatários",
			value: evt.recipients.map((item) => item?.nome || item?.name || item?.destinatario || String(item)).join(", ")
		});
		if (Array.isArray(evt.recipient_lawyers) && evt.recipient_lawyers.length > 0) meta.push({
			label: "Advogados",
			value: evt.recipient_lawyers.map((item) => {
				const lawyer = item?.advogado && typeof item.advogado === "object" ? item.advogado : item;
				const name = lawyer?.nome || lawyer?.name || "";
				const oab = lawyer?.numero_oab || lawyer?.numeroOab || lawyer?.oab || "";
				return [name, oab].filter(Boolean).join(" · ") || String(item);
			}).join(", ")
		});
		if (evt.status) meta.push({
			label: "Status DJEN",
			value: evt.status
		});
		if (evt.canceled_on) meta.push({
			label: "Cancelamento",
			value: evt.cancellation_reason ? `${formatDateDisplay(evt.canceled_on)} · ${evt.cancellation_reason}` : formatDateDisplay(evt.canceled_on)
		});
	} else {
		tipo = (evt.kind || "evento").toLowerCase();
		tipoLabel = evt.kind || "Evento";
		if (relevantAt) meta.push({
			label: "Data",
			value: `${dataExibicao}${horario ? " às " + horario : ""}`
		});
		if (evt.status) meta.push({
			label: "Status",
			value: evt.status
		});
	}
	return {
		id: evt.id,
		raw: evt,
		tipo,
		tipoLabel,
		titulo,
		processo,
		data: dateKey,
		dataExibicao,
		horario,
		status,
		tone,
		codicon,
		dotClass,
		urgencyClass,
		urgencyLevel,
		teor,
		meta,
		providencias
	};
}
var NAV_TABS = [
	{
		id: "eventos",
		label: "EVENTOS",
		icon: "calendar"
	},
	{
		id: "processos",
		label: "PROCESSOS",
		icon: "folder"
	},
	{
		id: "jurisprudencia",
		label: "JURISPRUDÊNCIA",
		icon: "book"
	},
	{
		id: "minutas",
		label: "MINUTAS",
		icon: "edit"
	}
];
var PROCESS_SECTIONS = [
	{
		id: "dossie",
		label: "Resumo"
	},
	{
		id: "timeline",
		label: "Movimentos"
	},
	{
		id: "pesquisa",
		label: "Pesquisa"
	},
	{
		id: "autos",
		label: "Autos"
	},
	{
		id: "pdf",
		label: "PDF"
	}
];
var AUTOS_INITIAL_BATCH = 10;
var AUTOS_RENDER_BATCH = 32;
var MARKDOWN_DOCUMENT_CSS = `
.markdown-document { margin: 0; color: inherit; background: transparent; font-family: inherit; font-size: .875rem; font-weight: 400; line-height: 1.5; overflow-wrap: break-word; }
.markdown-document > :first-child { margin-top: 0; }
.markdown-document > :last-child { margin-bottom: 0; }
.markdown-document a { color: inherit; text-decoration: none; }
.markdown-document a:hover { text-decoration: underline; }
.markdown-document strong { font-weight: 600; }
.markdown-document h1, .markdown-document h2, .markdown-document h3, .markdown-document h4, .markdown-document h5, .markdown-document h6 { margin-top: 18px; margin-bottom: 10px; font-weight: 600; line-height: 1.3; }
.markdown-document h1 { padding-bottom: .25em; font-size: 1.2142857em; border-bottom: 1px solid color-mix(in srgb, currentColor 18%, transparent); }
.markdown-document h2 { padding-bottom: .25em; font-size: 1.0714286em; border-bottom: 1px solid color-mix(in srgb, currentColor 18%, transparent); }
.markdown-document h3 { font-size: 1em; }
.markdown-document h4 { font-size: .95em; }
.markdown-document h5 { font-size: .9em; }
.markdown-document h6 { color: color-mix(in srgb, currentColor 65%, transparent); font-size: .85em; }
.markdown-document p, .markdown-document blockquote, .markdown-document ul, .markdown-document ol, .markdown-document table, .markdown-document pre { margin-top: 0; margin-bottom: 16px; }
.markdown-document p { text-align: justify; }
.markdown-document blockquote { padding: 0 1em; color: color-mix(in srgb, currentColor 65%, transparent); border-left: .25em solid color-mix(in srgb, currentColor 18%, transparent); }
.markdown-document blockquote > :first-child { margin-top: 0; }
.markdown-document blockquote > :last-child { margin-bottom: 0; }
.markdown-document ul, .markdown-document ol { padding-left: 2em; }
.markdown-document ul { list-style: disc; }
.markdown-document ol { list-style: decimal; }
.markdown-document ul ul, .markdown-document ul ol, .markdown-document ol ol, .markdown-document ol ul { margin-top: 0; margin-bottom: 0; }
.markdown-document li + li { margin-top: .25em; }
.markdown-document__table-wrap { overflow-x: auto; }
.markdown-document table { display: block; width: max-content; max-width: 100%; overflow: auto; border-spacing: 0; border-collapse: collapse; font-variant: tabular-nums; }
.markdown-document th, .markdown-document td { padding: 6px 13px; border: 1px solid color-mix(in srgb, currentColor 18%, transparent); }
.markdown-document th { font-weight: 600; }
.markdown-document tr { background: transparent; border-top: 1px solid color-mix(in srgb, currentColor 14%, transparent); }
.markdown-document tr:nth-child(2n) { background: color-mix(in srgb, currentColor 5%, transparent); }
.markdown-document code { padding: .2em .4em; margin: 0; font-family: "RobotoMono", ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace; font-size: 85%; white-space: break-spaces; background: color-mix(in srgb, currentColor 8%, transparent); border-radius: 6px; }
.markdown-document pre { padding: 16px; overflow: auto; font-family: "RobotoMono", ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace; font-size: 85%; line-height: 1.45; background: color-mix(in srgb, currentColor 6%, transparent); border-radius: 6px; }
.markdown-document pre > code { padding: 0; margin: 0; word-break: normal; white-space: pre; background: transparent; border: 0; }
.themis-scroll-visible { scrollbar-width: thin; scrollbar-color: color-mix(in srgb, currentColor 38%, transparent) transparent; }
.themis-scroll-visible::-webkit-scrollbar { width: 11px; }
.themis-scroll-visible::-webkit-scrollbar-track { background: transparent; }
.themis-scroll-visible::-webkit-scrollbar-thumb { min-height: 36px; background: color-mix(in srgb, currentColor 28%, transparent); border: 3px solid transparent; border-radius: 999px; background-clip: padding-box; }
.themis-scroll-visible:hover::-webkit-scrollbar-thumb { background-color: color-mix(in srgb, currentColor 46%, transparent); }
`;
function sourcePageKey(page) {
	const sourceRef = page?.source_ref || {};
	return `${sourceRef.document_id || page?.document_id || "page"}:${sourceRef.pdf_page || page?.page || ""}`;
}
function scrollOffsetWithinContainer(element, container) {
	if (!element || !container) return 0;
	const elementRect = element.getBoundingClientRect();
	const containerRect = container.getBoundingClientRect();
	return container.scrollTop + elementRect.top - containerRect.top - container.clientTop;
}
function scrollContainerToElement(element, container, extraOffset = 0) {
	if (!element || !container) return false;
	container.scrollTop = Math.max(0, scrollOffsetWithinContainer(element, container) + extraOffset);
	return true;
}
function decodeBase64Bytes(value) {
	const binary = atob(value);
	const bytes = new Uint8Array(binary.length);
	for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
	return bytes;
}
async function loadPluginAsset(ctx, assetPath) {
	const data = await ctx.rest(`/assets/${assetPath}`);
	if (!data?.content_base64) throw new Error(`Asset do plugin indisponível: ${assetPath}`);
	return {
		bytes: decodeBase64Bytes(data.content_base64),
		contentType: data.content_type || "application/octet-stream",
		contentBase64: data.content_base64
	};
}
var PDFJS_TOOLBAR_ICONS = [
	"findbarButton-next.svg",
	"findbarButton-previous.svg",
	"secondaryToolbarButton-rotateCcw.svg",
	"secondaryToolbarButton-rotateCw.svg",
	"toolbarButton-pageDown.svg",
	"toolbarButton-pageUp.svg",
	"toolbarButton-print.svg",
	"toolbarButton-search.svg",
	"toolbarButton-zoomIn.svg",
	"toolbarButton-zoomOut.svg"
];
var PDFJS_TOOLBAR_CSS = `
.themis-pdf-shell { position: relative; min-height: 0; flex: 1 1 auto; overflow: hidden; }
.themis-pdf-toolbar { height: 36px; display: flex; align-items: center; gap: 3px; padding: 3px 6px; border-bottom: 1px solid var(--ui-stroke-secondary); background: var(--ui-bg-secondary, var(--background)); color: var(--ui-text-secondary, currentColor); overflow-x: auto; overflow-y: hidden; }
.themis-pdf-toolbar .toolbarHorizontalGroup { display: inline-flex; align-items: center; gap: 2px; flex: 0 0 auto; }
.themis-pdf-toolbar .toolbarSeparator { width: 1px; height: 20px; margin: 0 3px; background: var(--ui-stroke-secondary); opacity: .7; }
.themis-pdf-toolbar .toolbarButton { position: relative; width: 28px; height: 28px; padding: 0; border: 0; border-radius: 4px; background: transparent; color: inherit; cursor: pointer; }
.themis-pdf-toolbar .toolbarButton:hover, .themis-pdf-toolbar .toolbarButton:focus-visible { background: var(--ui-bg-hover, color-mix(in srgb, currentColor 10%, transparent)); outline: none; }
.themis-pdf-toolbar .toolbarButton:disabled { cursor: default; opacity: .35; }
.themis-pdf-toolbar .toolbarButton::before { content: ''; position: absolute; inset: 6px; background: currentColor; -webkit-mask: var(--themis-pdf-icon) center / contain no-repeat; mask: var(--themis-pdf-icon) center / contain no-repeat; }
.themis-pdf-toolbar #previous { --themis-pdf-icon: url('/api/plugins/themis/assets/pdfjs/images/toolbarButton-pageUp.svg'); }
.themis-pdf-toolbar #next { --themis-pdf-icon: url('/api/plugins/themis/assets/pdfjs/images/toolbarButton-pageDown.svg'); }
.themis-pdf-toolbar #zoomOut { --themis-pdf-icon: url('/api/plugins/themis/assets/pdfjs/images/toolbarButton-zoomOut.svg'); }
.themis-pdf-toolbar #zoomIn { --themis-pdf-icon: url('/api/plugins/themis/assets/pdfjs/images/toolbarButton-zoomIn.svg'); }
.themis-pdf-toolbar #viewFind { --themis-pdf-icon: url('/api/plugins/themis/assets/pdfjs/images/toolbarButton-search.svg'); }
.themis-pdf-toolbar #pageRotateCcw { --themis-pdf-icon: url('/api/plugins/themis/assets/pdfjs/images/secondaryToolbarButton-rotateCcw.svg'); }
.themis-pdf-toolbar #pageRotateCw { --themis-pdf-icon: url('/api/plugins/themis/assets/pdfjs/images/secondaryToolbarButton-rotateCw.svg'); }
.themis-pdf-toolbar #print { --themis-pdf-icon: url('/api/plugins/themis/assets/pdfjs/images/toolbarButton-print.svg'); }
.themis-pdf-toolbar .toolbarField { height: 24px; border: 1px solid var(--ui-stroke-secondary); border-radius: 4px; background: var(--ui-bg-primary, var(--background)); color: var(--ui-text-primary, currentColor); font-size: 11px; }
.themis-pdf-toolbar #pageNumber { width: 44px; padding: 0 4px; text-align: center; }
.themis-pdf-toolbar .toolbarLabel { min-width: 42px; padding: 0 3px; font-size: 11px; white-space: nowrap; color: var(--ui-text-tertiary, currentColor); }
.themis-pdf-toolbar .toolbarTextButton { width: auto; min-width: 36px; padding: 0 6px; font-size: 10px; font-weight: 600; }
.themis-pdf-toolbar .toolbarTextButton::before { display: none; }
.themis-pdf-findbar { position: absolute; z-index: 4; top: 39px; left: 6px; display: flex; align-items: center; gap: 3px; padding: 5px; border: 1px solid var(--ui-stroke-secondary); border-radius: 5px; background: var(--ui-bg-secondary, var(--background)); box-shadow: 0 6px 18px color-mix(in srgb, black 20%, transparent); }
.themis-pdf-findbar #findInput { width: 190px; padding: 0 7px; }
.themis-pdf-findbar .toolbarButton { position: relative; width: 28px; height: 24px; border: 0; border-radius: 4px; background: transparent; color: inherit; cursor: pointer; }
.themis-pdf-findbar .toolbarButton::before { content: ''; position: absolute; inset: 5px 7px; background: currentColor; -webkit-mask: var(--themis-pdf-icon) center / contain no-repeat; mask: var(--themis-pdf-icon) center / contain no-repeat; }
.themis-pdf-findbar #findPreviousButton { --themis-pdf-icon: url('/api/plugins/themis/assets/pdfjs/images/findbarButton-previous.svg'); }
.themis-pdf-findbar #findNextButton { --themis-pdf-icon: url('/api/plugins/themis/assets/pdfjs/images/findbarButton-next.svg'); }
.themis-pdf-findbar .findResults { max-width: 100px; font-size: 10px; color: var(--ui-text-tertiary, currentColor); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
`;
async function loadPdfJsRuntime(ctx) {
	const [worker, css] = await Promise.all([loadPluginAsset(ctx, "pdfjs/pdf.worker.min.mjs"), loadPluginAsset(ctx, "pdfjs/pdf_viewer.css")]);
	const workerUrl = URL.createObjectURL(new Blob([worker.bytes], { type: "text/javascript" }));
	try {
		const sourceCss = new TextDecoder().decode(css.bytes);
		const cssImageNames = Array.from(sourceCss.matchAll(/url\(\s*['"]?images\/([^)'"\s]+)/g), (match) => match[1]);
		const imageNames = [.../* @__PURE__ */ new Set([...cssImageNames, ...PDFJS_TOOLBAR_ICONS])];
		const imageAssets = await Promise.all(imageNames.map((name) => loadPluginAsset(ctx, `pdfjs/images/${name}`)));
		let cssText = sourceCss;
		let toolbarCss = PDFJS_TOOLBAR_CSS;
		imageNames.forEach((name, index) => {
			const icon = imageAssets[index];
			const dataUrl = `data:${icon.contentType};base64,${icon.contentBase64}`;
			cssText = cssText.replaceAll(`images/${name}`, dataUrl);
			toolbarCss = toolbarCss.replaceAll(`/api/plugins/themis/assets/pdfjs/images/${name}`, dataUrl);
		});
		return {
			module: pdfjs_viewer_bundle_exports,
			workerUrl,
			cssText: `${cssText}\n${toolbarCss}`
		};
	} catch (error) {
		URL.revokeObjectURL(workerUrl);
		throw error;
	}
}
function PdfJsViewer({ pdfData, runtimePromise, pageNumber = 1, active = false, onPageChange, onError }) {
	const containerRef = useRef(null);
	const viewerRef = useRef(null);
	const eventBusRef = useRef(null);
	const pagesReadyRef = useRef(false);
	const pendingPageRef = useRef(Math.max(1, Number(pageNumber) || 1));
	const printUrlRef = useRef("");
	const printFrameRef = useRef(null);
	const [currentPage, setCurrentPage] = useState(pendingPageRef.current);
	const [pageInput, setPageInput] = useState(String(pendingPageRef.current));
	const [pagesCount, setPagesCount] = useState(0);
	const [scaleLabel, setScaleLabel] = useState("100%");
	const [rotation, setRotation] = useState(0);
	const [findOpen, setFindOpen] = useState(false);
	const [findQuery, setFindQuery] = useState("");
	const [findResult, setFindResult] = useState("");
	pendingPageRef.current = Math.max(1, Number(pageNumber) || 1);
	useEffect(() => {
		setPageInput(String(pendingPageRef.current));
	}, [pageNumber]);
	useEffect(() => {
		if (!active) return void 0;
		const frameId = requestAnimationFrame(() => {
			const viewer = viewerRef.current;
			if (!viewer || !pagesReadyRef.current) return;
			const pageCount = viewer.pagesCount || viewer.pdfDocument?.numPages || pendingPageRef.current;
			const targetPage = Math.min(pendingPageRef.current, pageCount);
			viewer.currentScaleValue = viewer.currentScaleValue || "page-width";
			viewer.update();
			viewer.scrollPageIntoView({ pageNumber: targetPage });
		});
		return () => cancelAnimationFrame(frameId);
	}, [
		active,
		pdfData,
		pageNumber
	]);
	const goToPage = (value) => {
		const viewer = viewerRef.current;
		if (!viewer || !pagesReadyRef.current) return;
		const target = Math.max(1, Math.min(Number(value) || 1, viewer.pagesCount || pagesCount || 1));
		pendingPageRef.current = target;
		setPageInput(String(target));
		viewer.currentPageNumber = target;
	};
	const setViewerScale = (value) => {
		const viewer = viewerRef.current;
		if (viewer && pagesReadyRef.current) viewer.currentScaleValue = value;
	};
	const dispatchFind = (query, findPrevious = false, type = "again") => {
		const eventBus = eventBusRef.current;
		if (!eventBus || !query) return;
		eventBus.dispatch("find", {
			source: containerRef.current,
			type,
			query,
			phraseSearch: true,
			caseSensitive: false,
			entireWord: false,
			highlightAll: true,
			findPrevious
		});
	};
	const closeFind = () => {
		setFindOpen(false);
		eventBusRef.current?.dispatch("findbarclose", { source: containerRef.current });
	};
	const rotatePages = (delta) => {
		const viewer = viewerRef.current;
		if (!viewer || !pagesReadyRef.current) return;
		viewer.pagesRotation = (viewer.pagesRotation + delta + 360) % 360;
	};
	const cleanupPrintFrame = () => {
		const active = printFrameRef.current;
		if (!active) return;
		if (active.timer) clearTimeout(active.timer);
		if (active.frame?.parentNode) active.frame.parentNode.removeChild(active.frame);
		printFrameRef.current = null;
	};
	const printPdf = () => {
		if (!printUrlRef.current) return;
		cleanupPrintFrame();
		const frame = document.createElement("iframe");
		frame.setAttribute("aria-hidden", "true");
		frame.style.cssText = "position:fixed;width:1px;height:1px;right:0;bottom:0;border:0;opacity:0;pointer-events:none";
		frame.src = printUrlRef.current;
		document.body.appendChild(frame);
		const timer = window.setTimeout(cleanupPrintFrame, 12e4);
		printFrameRef.current = {
			frame,
			timer
		};
		frame.onload = () => {
			window.setTimeout(() => {
				try {
					frame.contentWindow?.focus();
					frame.contentWindow?.print();
				} catch (error) {
					onError?.(error);
					cleanupPrintFrame();
				}
			}, 150);
		};
	};
	useEffect(() => {
		if (!pdfData || !runtimePromise || !containerRef.current) return void 0;
		let cancelled = false;
		let loadingTask = null;
		let pdfDocument = null;
		let viewer = null;
		let eventBus = null;
		let pagesInitHandler = null;
		let pageChangingHandler = null;
		let scaleChangingHandler = null;
		let rotationChangingHandler = null;
		let findMatchesHandler = null;
		let findStateHandler = null;
		const printableBytes = pdfData.slice();
		printUrlRef.current = URL.createObjectURL(new Blob([printableBytes], { type: "application/pdf" }));
		setCurrentPage(pendingPageRef.current);
		setPageInput(String(pendingPageRef.current));
		setPagesCount(0);
		setScaleLabel("100%");
		setRotation(0);
		setFindOpen(false);
		setFindQuery("");
		setFindResult("");
		Promise.resolve(runtimePromise).then(async (runtime) => {
			if (cancelled || !containerRef.current) return;
			const { EventBus, PDFFindController, PDFLinkService, PDFRenderingQueue, PDFViewer, GlobalWorkerOptions, getDocument } = runtime.module;
			if (!EventBus || !PDFFindController || !PDFLinkService || !PDFRenderingQueue || !PDFViewer || !getDocument) throw new Error("Bundle PDF.js sem os componentes oficiais esperados");
			GlobalWorkerOptions.workerSrc = runtime.workerUrl;
			eventBus = new EventBus();
			eventBusRef.current = eventBus;
			const linkService = new PDFLinkService({ eventBus });
			const findController = new PDFFindController({
				linkService,
				eventBus
			});
			const renderingQueue = new PDFRenderingQueue();
			viewer = new PDFViewer({
				container: containerRef.current,
				viewer: containerRef.current.querySelector(".pdfViewer"),
				eventBus,
				linkService,
				findController,
				renderingQueue,
				textLayerMode: 2,
				removePageBorders: false
			});
			linkService.setViewer(viewer);
			renderingQueue.setViewer(viewer);
			pageChangingHandler = (event) => {
				if (cancelled || !Number.isInteger(event?.pageNumber)) return;
				setCurrentPage(event.pageNumber);
				setPageInput(String(event.pageNumber));
				onPageChange?.(event.pageNumber);
			};
			scaleChangingHandler = (event) => {
				if (cancelled || !Number.isFinite(event?.scale)) return;
				setScaleLabel(`${Math.round(event.scale * 100)}%`);
			};
			rotationChangingHandler = (event) => {
				if (!cancelled && Number.isInteger(event?.pagesRotation)) setRotation(event.pagesRotation);
			};
			findMatchesHandler = (event) => {
				if (cancelled) return;
				const count = event?.matchesCount;
				setFindResult(count?.total ? `${count.current || 0} de ${count.total}` : "");
			};
			findStateHandler = (event) => {
				if (cancelled) return;
				const count = event?.matchesCount;
				if (count?.total) setFindResult(`${count.current || 0} de ${count.total}`);
				else if (event?.state === 1) setFindResult("Não encontrado");
			};
			eventBus.on("pagechanging", pageChangingHandler);
			eventBus.on("scalechanging", scaleChangingHandler);
			eventBus.on("rotationchanging", rotationChangingHandler);
			eventBus.on("updatefindmatchescount", findMatchesHandler);
			eventBus.on("updatefindcontrolstate", findStateHandler);
			pagesInitHandler = () => {
				if (cancelled || !viewer) return;
				pagesReadyRef.current = true;
				viewerRef.current = viewer;
				const pageCount = viewer.pagesCount || pdfDocument?.numPages || pendingPageRef.current;
				setPagesCount(pageCount);
				viewer.currentPageNumber = Math.min(pendingPageRef.current, pageCount);
				viewer.currentScaleValue = "page-width";
			};
			eventBus.on("pagesinit", pagesInitHandler);
			loadingTask = getDocument({
				data: pdfData,
				isEvalSupported: false,
				enableXfa: false
			});
			pdfDocument = await loadingTask.promise;
			if (cancelled) return;
			linkService.setDocument(pdfDocument);
			viewer.setDocument(pdfDocument);
		}).catch((error) => {
			if (!cancelled) onError?.(error);
		});
		return () => {
			cancelled = true;
			pagesReadyRef.current = false;
			viewerRef.current = null;
			eventBusRef.current = null;
			if (eventBus && pagesInitHandler) eventBus.off("pagesinit", pagesInitHandler);
			if (eventBus && pageChangingHandler) eventBus.off("pagechanging", pageChangingHandler);
			if (eventBus && scaleChangingHandler) eventBus.off("scalechanging", scaleChangingHandler);
			if (eventBus && rotationChangingHandler) eventBus.off("rotationchanging", rotationChangingHandler);
			if (eventBus && findMatchesHandler) eventBus.off("updatefindmatchescount", findMatchesHandler);
			if (eventBus && findStateHandler) eventBus.off("updatefindcontrolstate", findStateHandler);
			eventBus?.dispatch("pagesdestroy", {});
			loadingTask?.destroy?.();
			pdfDocument?.destroy?.();
			viewer?.cleanup?.();
			cleanupPrintFrame();
			if (printUrlRef.current) URL.revokeObjectURL(printUrlRef.current);
			printUrlRef.current = "";
		};
	}, [pdfData, runtimePromise]);
	const toolbarButton = (id, title, onClick, disabled = false) => jsx("button", {
		id,
		type: "button",
		className: "toolbarButton",
		title,
		"aria-label": title,
		disabled,
		onClick,
		children: jsx("span", {
			className: "sr-only",
			children: title
		})
	});
	return jsxs("div", {
		className: "themis-pdf-shell",
		children: [
			jsxs("div", {
				id: "toolbarContainer",
				className: "themis-pdf-toolbar",
				children: [
					jsxs("div", {
						className: "toolbarHorizontalGroup",
						children: [
							toolbarButton("previous", "Página anterior", () => goToPage(currentPage - 1), currentPage <= 1),
							jsx("input", {
								id: "pageNumber",
								className: "toolbarField",
								type: "text",
								inputMode: "numeric",
								pattern: "[0-9]*",
								value: pageInput,
								title: "Página",
								"aria-label": "Página atual",
								onChange: (event) => setPageInput(event.target.value),
								onKeyDown: (event) => {
									if (event.key === "Enter") goToPage(event.currentTarget.value);
								},
								onBlur: (event) => goToPage(event.currentTarget.value)
							}),
							jsx("span", {
								className: "toolbarLabel",
								children: `de ${pagesCount || "—"}`
							}),
							toolbarButton("next", "Próxima página", () => goToPage(currentPage + 1), !pagesCount || currentPage >= pagesCount)
						]
					}),
					jsx("span", { className: "toolbarSeparator" }),
					jsxs("div", {
						className: "toolbarHorizontalGroup",
						children: [
							toolbarButton("zoomOut", "Reduzir", () => viewerRef.current?.decreaseScale()),
							jsx("span", {
								className: "toolbarLabel",
								children: scaleLabel
							}),
							toolbarButton("zoomIn", "Ampliar", () => viewerRef.current?.increaseScale()),
							jsx("button", {
								type: "button",
								className: "toolbarButton toolbarTextButton",
								title: "Largura da página",
								onClick: () => setViewerScale("page-width"),
								children: "Largura"
							}),
							jsx("button", {
								type: "button",
								className: "toolbarButton toolbarTextButton",
								title: "Ajustar página",
								onClick: () => setViewerScale("page-fit"),
								children: "Página"
							}),
							jsx("button", {
								type: "button",
								className: "toolbarButton toolbarTextButton",
								title: "Tamanho real",
								onClick: () => setViewerScale("page-actual"),
								children: "100%"
							})
						]
					}),
					jsx("span", { className: "toolbarSeparator" }),
					jsxs("div", {
						className: "toolbarHorizontalGroup",
						children: [
							toolbarButton("viewFind", "Localizar no documento", () => setFindOpen((value) => !value)),
							toolbarButton("pageRotateCcw", `Girar à esquerda (${rotation}°)`, () => rotatePages(-90)),
							toolbarButton("pageRotateCw", `Girar à direita (${rotation}°)`, () => rotatePages(90)),
							toolbarButton("print", "Imprimir PDF", printPdf)
						]
					})
				]
			}),
			findOpen ? jsxs("div", {
				id: "findbar",
				className: "themis-pdf-findbar",
				children: [
					jsx("input", {
						id: "findInput",
						className: "toolbarField",
						value: findQuery,
						autoFocus: true,
						placeholder: "Localizar no documento…",
						"aria-label": "Localizar no documento",
						onChange: (event) => {
							const query = event.target.value;
							setFindQuery(query);
							setFindResult("");
							if (query) dispatchFind(query, false, "");
						},
						onKeyDown: (event) => {
							if (event.key === "Enter") dispatchFind(event.currentTarget.value, event.shiftKey, "again");
							if (event.key === "Escape") closeFind();
						}
					}),
					toolbarButton("findPreviousButton", "Ocorrência anterior", () => dispatchFind(findQuery, true, "again"), !findQuery),
					toolbarButton("findNextButton", "Próxima ocorrência", () => dispatchFind(findQuery, false, "again"), !findQuery),
					jsx("span", {
						className: "findResults",
						"aria-live": "polite",
						children: findResult
					}),
					jsx("button", {
						type: "button",
						className: "toolbarButton toolbarTextButton",
						title: "Fechar busca",
						onClick: closeFind,
						children: "×"
					})
				]
			}) : null,
			jsx("div", {
				ref: containerRef,
				className: "pdfjs-viewer-container absolute inset-x-0 bottom-0 overflow-auto bg-background",
				"data-themis-page-scroll": "true",
				style: {
					position: "absolute",
					top: "36px",
					right: 0,
					bottom: 0,
					left: 0
				},
				children: jsx("div", { className: "pdfViewer" })
			})
		]
	});
}
function ProcessosView({ ctx, navTarget = null, onNavigateAutos, onNavigatePdf }) {
	const pluginCtxRef = useRef(ctx);
	pluginCtxRef.current = ctx;
	const focusedSessionId = useValue(host.state.focusedSessionId);
	const activeSessionId = useValue(host.state.activeSessionId);
	const modelSessionId = focusedSessionId || activeSessionId || null;
	const [processes, setProcesses] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);
	const [selectedPid, setSelectedPid] = useState(() => navTarget?.process_id || ctx.storage.get("workspace.process.selectedId", ""));
	const [search, setSearch] = useState("");
	const [activeSection, setActiveSection] = useState(() => navTarget?.section || ctx.storage.get("workspace.process.view", "dossie"));
	const [listWidthPct, setListWidthPct] = useState(30);
	const [isDragging, setIsDragging] = useState(false);
	const splitContainerRef = useRef(null);
	const autosScrollRef = useRef(null);
	const autosPageRefs = useRef({});
	const autosRestoreKeyRef = useRef("");
	const autosScrollTimerRef = useRef(null);
	const processInFlightRef = useRef({
		overview: {},
		movements: {},
		summaries: {},
		summaryStatus: {},
		caseSynthesis: {},
		autos: {},
		pdf: {}
	});
	const selectedPidRef = useRef(selectedPid);
	selectedPidRef.current = selectedPid;
	const processSelectionRef = useRef({
		pid: selectedPid,
		epoch: 0
	});
	if (processSelectionRef.current.pid !== selectedPid) processSelectionRef.current = {
		pid: selectedPid,
		epoch: processSelectionRef.current.epoch + 1
	};
	const processTreeSignatureRef = useRef("");
	const [processRefreshRevision, setProcessRefreshRevision] = useState(0);
	const pdfBytesRef = useRef(null);
	const pdfProcessIdRef = useRef("");
	const pdfJsRuntimeRef = useRef({
		promise: null,
		runtime: null,
		style: null
	});
	const pdfNavigationActionsRef = useRef({
		saveAutosReading: null,
		openPdfAtPage: null
	});
	const [overviews, setOverviews] = useState({});
	const [movements, setMovements] = useState({});
	const [movementSummaries, setMovementSummaries] = useState({});
	const [summaryLoading, setSummaryLoading] = useState({});
	const [summaryErrors, setSummaryErrors] = useState({});
	const [expandedMovementSummaries, setExpandedMovementSummaries] = useState({});
	const [summaryConfirmationMovement, setSummaryConfirmationMovement] = useState(null);
	const [processSummaryConfirmation, setProcessSummaryConfirmation] = useState(null);
	const [processSummaryJob, setProcessSummaryJob] = useState(null);
	const processSummaryBusyRef = useRef(false);
	const [summaryStatuses, setSummaryStatuses] = useState({});
	const [summaryStatusReady, setSummaryStatusReady] = useState(null);
	const [summaryStatusError, setSummaryStatusError] = useState(null);
	const [caseSyntheses, setCaseSyntheses] = useState({});
	const [caseSynthesisJobs, setCaseSynthesisJobs] = useState({});
	const [modelMenuOpen, setModelMenuOpen] = useState(false);
	const [aiModelOverride, setAiModelOverride] = useState({
		effort: DEFAULT_REASONING_EFFORT,
		model: "",
		provider: ""
	});
	const [sessionAiModel, setSessionAiModel] = useState(null);
	const [expandedMovements, setExpandedMovements] = useState({});
	const [autos, setAutos] = useState({});
	const [loadingSection, setLoadingSection] = useState(false);
	const [visibleAutosPages, setVisibleAutosPages] = useState({});
	const [pdfView, setPdfView] = useState(() => ctx.storage.get("workspace.pdf.current", null));
	const [pdfData, setPdfData] = useState(null);
	const [pdfLoading, setPdfLoading] = useState(false);
	const [pdfError, setPdfError] = useState(null);
	useEffect(() => {
		if (activeSection !== "pesquisa") return void 0;
		pluginCtxRef.current.rest("/embedding/cancel_idle", { method: "POST" }).catch(() => {});
		return () => {
			pluginCtxRef.current.rest("/embedding/idle", { method: "POST" }).catch(() => {});
		};
	}, [activeSection]);
	useEffect(() => {
		let mounted = true;
		const params = { explicit_only: true };
		if (modelSessionId) params.session_id = modelSessionId;
		host.request("model.options", params).then((options) => {
			if (!mounted) return;
			const provider = String(options?.provider || "").trim();
			const model = String(options?.model || "").trim();
			setSessionAiModel(provider && model ? {
				provider,
				model
			} : null);
		}).catch(() => {
			if (mounted) setSessionAiModel(null);
		});
		return () => {
			mounted = false;
		};
	}, [modelSessionId]);
	const hasExplicitAiOverride = Boolean(aiModelOverride.model && aiModelOverride.provider);
	const selectedAiModel = hasExplicitAiOverride ? {
		model: aiModelOverride.model,
		provider: aiModelOverride.provider
	} : sessionAiModel;
	const resolveAiModelForJob = async () => {
		if (hasExplicitAiOverride) return {
			provider: aiModelOverride.provider,
			model: aiModelOverride.model
		};
		const params = { explicit_only: true };
		if (modelSessionId) params.session_id = modelSessionId;
		const options = await host.request("model.options", params);
		const provider = String(options?.provider || "").trim();
		const model = String(options?.model || "").trim();
		if (!provider || !model) throw new Error("Hermes não retornou o provider/model atualmente selecionado");
		const selection = {
			provider,
			model
		};
		setSessionAiModel(selection);
		return selection;
	};
	const selectedEffortLabel = aiModelOverride.effort ? reasoningEffortLabel(aiModelOverride.effort) : "";
	const modelTriggerLabel = selectedAiModel?.model ? `${selectedAiModel.model}${selectedEffortLabel ? ` · ${selectedEffortLabel}` : ""}` : "Modelo";
	/** @type {import('@hermes/plugin-sdk').ModelMenuController} */
	const modelMenuController = {
		applyPreset: (preset, row) => {
			setAiModelOverride({
				effort: preset.effort ?? "",
				model: row.model,
				provider: row.provider
			});
		},
		current: {
			effort: aiModelOverride.effort,
			fast: false,
			model: selectedAiModel?.model || "",
			provider: selectedAiModel?.provider || ""
		},
		presetFor: () => ({}),
		select: (model, provider) => {
			setAiModelOverride((current) => ({
				...current,
				model,
				provider
			}));
		},
		setOptions: (patch, row) => {
			if (patch.effort !== void 0) setAiModelOverride({
				effort: patch.effort,
				model: row.model,
				provider: row.provider
			});
		}
	};
	useEffect(() => {
		if (!navTarget) return;
		if (navTarget.process_id && navTarget.process_id !== selectedPid) setSelectedPid(navTarget.process_id);
		if (navTarget.section) setActiveSection(navTarget.section);
		else if (navTarget.document_id || navTarget.pdf_page) setActiveSection("autos");
	}, [navTarget]);
	useEffect(() => {
		let isMounted = true;
		let firstLoad = true;
		let treeRequestInFlight = false;
		const loadProcessTree = () => {
			if (treeRequestInFlight) return;
			treeRequestInFlight = true;
			if (firstLoad) setLoading(true);
			ctx.rest("/tree").then((data) => {
				if (!isMounted) return;
				const procs = Array.isArray(data?.processes) ? data.processes : [];
				const signature = JSON.stringify(procs.map((process) => ({
					id: process.process_id || process.id || "",
					status: process.status || "",
					pipeline_status: process.pipeline_status || "",
					pipeline_revision: process.pipeline_revision || "",
					updated_at: process.updated_at || "",
					label: process.label || "",
					movements: process.children?.find((child) => child.node_type === "movement_collection")?.children?.length || 0,
					documents: process.children?.find((child) => child.node_type === "document_collection")?.children?.length || 0
				})));
				const treeChanged = Boolean(processTreeSignatureRef.current && processTreeSignatureRef.current !== signature);
				processTreeSignatureRef.current = signature;
				setProcesses(procs);
				setError(null);
				setLoading(false);
				firstLoad = false;
				const currentPid = selectedPidRef.current;
				const currentPidExists = currentPid && procs.some((process) => (process.process_id || process.id) === currentPid);
				if (currentPid && !currentPidExists) {
					ctx.storage.remove("workspace.process.selectedId");
					setSelectedPid(procs.length > 0 ? (procs[0].process_id || procs[0].id) : "");
				} else if (!currentPid && procs.length > 0) {
					setSelectedPid(procs[0].process_id || procs[0].id);
				}
				if (treeChanged && selectedPidRef.current && procs.some((process) => (process.process_id || process.id) === selectedPidRef.current)) setProcessRefreshRevision((previous) => previous + 1);
			}).catch((err) => {
				if (!isMounted) return;
				console.error("[Themis] Erro ao atualizar processos (/tree):", err);
				if (firstLoad) {
					setError(err.message || String(err));
					setProcesses([]);
					setLoading(false);
					firstLoad = false;
				}
			}).finally(() => {
				treeRequestInFlight = false;
			});
		};
		loadProcessTree();
		const refreshTimer = setInterval(loadProcessTree, 3e3);
		return () => {
			isMounted = false;
			clearInterval(refreshTimer);
		};
	}, [ctx]);
	useEffect(() => {
		if (!selectedPid) return;
		const pid = selectedPid;
		const selectionEpoch = processSelectionRef.current.epoch;
		const isCurrent = () => selectedPidRef.current === pid && processSelectionMatches(processSelectionRef.current, pid, selectionEpoch);
		const inFlight = processInFlightRef.current;
		const requestJson = (kind, url, setter, normalize = (value) => value) => {
			if (inFlight[kind][pid]?.epoch === selectionEpoch) return inFlight[kind][pid].request;
			const request = ctx.rest(url).then((data) => {
				if (!isCurrent()) return data;
				if (kind === "summaryStatus") setProcessSummaryJob((previous) => movementAnalysisJobForStatusUpdate(previous, pid, data, processSummaryBusyRef.current));
				if (kind === "caseSynthesis") {
					const job = data?.job;
					const jobStatus = String(job?.status || "").toUpperCase();
					setCaseSynthesisJobs((previous) => ({
						...previous,
						[pid]: ["PENDING", "RUNNING"].includes(jobStatus) ? job : jobStatus === "COMPLETED" && job?.synthesis_id && data?.synthesis?.synthesis_id === job.synthesis_id ? {
							...job,
							status: "RUNNING",
							applying_result: true
						} : null
					}));
					if (["FAILED", "PARTIAL"].includes(jobStatus)) setSummaryErrors((previous) => ({
						...previous,
						[`__case__:${pid}`]: job?.error || `Geração da síntese ${jobStatus.toLowerCase()}`
					}));
					else if (jobStatus === "COMPLETED" && job?.synthesis_id && data?.synthesis?.synthesis_id !== job.synthesis_id) setSummaryErrors((previous) => ({
						...previous,
						[`__case__:${pid}`]: "O job concluiu, mas a síntese correspondente não foi localizada"
					}));
				}
				setter((previous) => ({
					...previous,
					[pid]: normalize(data)
				}));
				if (kind === "caseSynthesis" && String(data?.job?.status || "").toUpperCase() === "COMPLETED" && data?.job?.synthesis_id && data?.synthesis?.synthesis_id === data.job.synthesis_id) setCaseSynthesisJobs((previous) => ({
					...previous,
					[pid]: null
				}));
				if (kind === "summaryStatus") {
					setSummaryStatusReady({
						pid,
						epoch: selectionEpoch
					});
					setSummaryStatusError(null);
				}
				return data;
			}).catch((error) => {
				if (isCurrent()) {
					console.error(`[Themis] Erro ao pré-carregar ${kind}:`, error);
					if (kind === "summaryStatus") setSummaryStatusError({
						pid,
						epoch: selectionEpoch
					});
				}
				return null;
			}).finally(() => {
				if (inFlight[kind][pid]?.request === request) delete inFlight[kind][pid];
				if (isCurrent()) setLoadingSection(false);
			});
			inFlight[kind][pid] = {
				epoch: selectionEpoch,
				request
			};
			return request;
		};
		setLoadingSection(true);
		requestJson("overview", `/processes/${encodeURIComponent(pid)}/overview`, setOverviews);
		requestJson("movements", `/processes/${encodeURIComponent(pid)}/movements`, setMovements, normalizeMovementsResponse);
		requestJson("summaries", `/processes/${encodeURIComponent(pid)}/summaries`, setMovementSummaries, (value) => value?.summaries || {});
		requestJson("summaryStatus", `/processes/${encodeURIComponent(pid)}/summaries/status`, setSummaryStatuses);
		requestJson("caseSynthesis", `/processes/${encodeURIComponent(pid)}/case-synthesis`, setCaseSyntheses);
		requestJson("autos", `/processes/${encodeURIComponent(pid)}/autos`, setAutos);
	}, [
		ctx,
		selectedPid,
		processRefreshRevision
	]);
	useEffect(() => {
		const pid = selectedPid;
		const jobId = caseSynthesisJobs[pid]?.job_id;
		if (!pid || !jobId) return void 0;
		let active = true;
		let pollInFlight = false;
		const poll = async () => {
			if (pollInFlight) return;
			pollInFlight = true;
			try {
				const job = await ctx.rest(`/processes/${encodeURIComponent(pid)}/case-synthesis/jobs/${encodeURIComponent(jobId)}`);
				if (!active || selectedPidRef.current !== pid) return;
				const status = String(job?.status || "").toUpperCase();
				if (["PENDING", "RUNNING"].includes(status)) {
					setCaseSynthesisJobs((previous) => ({
						...previous,
						[pid]: job
					}));
					return;
				}
				if (status === "COMPLETED") {
					const value = await ctx.rest(`/processes/${encodeURIComponent(pid)}/case-synthesis`);
					if (!value?.synthesis || job?.synthesis_id && value.synthesis.synthesis_id !== job.synthesis_id) {
						if (active && selectedPidRef.current === pid) {
							setSummaryErrors((previous) => ({
								...previous,
								[`__case__:${pid}`]: "O job concluiu, mas a síntese correspondente não foi localizada"
							}));
							setCaseSynthesisJobs((previous) => ({
								...previous,
								[pid]: null
							}));
						}
						return;
					}
					if (active && selectedPidRef.current === pid) {
						setCaseSyntheses((previous) => ({
							...previous,
							[pid]: value
						}));
						setCaseSynthesisJobs((previous) => ({
							...previous,
							[pid]: null
						}));
						setSummaryErrors((previous) => ({
							...previous,
							[`__case__:${pid}`]: null
						}));
					}
				} else if (["FAILED", "PARTIAL"].includes(status)) {
					setSummaryErrors((previous) => ({
						...previous,
						[`__case__:${pid}`]: job?.error || "Falha ao gerar a síntese do caso"
					}));
					setCaseSynthesisJobs((previous) => ({
						...previous,
						[pid]: null
					}));
				}
			} catch (error) {
				if (active) console.error("[Themis] Erro ao consultar job de síntese do caso:", error);
			} finally {
				pollInFlight = false;
			}
		};
		poll();
		const timer = setInterval(poll, 1200);
		return () => {
			active = false;
			clearInterval(timer);
		};
	}, [
		ctx,
		selectedPid,
		caseSynthesisJobs[selectedPid]?.job_id
	]);
	useEffect(() => {
		const pid = selectedPid;
		if (!pid || !movementAnalysisJobIsActive(processSummaryJob)) return;
		const jobId = processSummaryJob?.job_id;
		if (!jobId) return;
		let active = true;
		let refreshingFinal = false;
		const refreshFinal = async () => {
			if (refreshingFinal) return;
			refreshingFinal = true;
			try {
				const status = await ctx.rest(`/processes/${encodeURIComponent(pid)}/summaries/status`);
				if (!active || selectedPidRef.current !== pid) return;
				setSummaryStatuses((previous) => ({
					...previous,
					[pid]: status
				}));
				const refreshedMovements = normalizeMovementsResponse(await ctx.rest(`/processes/${encodeURIComponent(pid)}/movements`));
				if (!active || selectedPidRef.current !== pid) return;
				setMovements((previous) => ({
					...previous,
					[pid]: refreshedMovements
				}));
				const summaries = await ctx.rest(`/processes/${encodeURIComponent(pid)}/summaries`);
				if (active && selectedPidRef.current === pid) setMovementSummaries((previous) => ({
					...previous,
					[pid]: summaries?.summaries || {}
				}));
			} catch (error) {
				if (active) console.error("[Themis] Erro ao atualizar resumos após o job:", error);
			}
		};
		let pollInFlight = false;
		const poll = async () => {
			if (pollInFlight) return;
			pollInFlight = true;
			try {
				const job = await ctx.rest(`/processes/${encodeURIComponent(pid)}/summaries/jobs/${encodeURIComponent(jobId)}`);
				if (!active || selectedPidRef.current !== pid) return;
				if (!movementAnalysisJobIsActive(job)) {
					await refreshFinal();
					if (active && selectedPidRef.current === pid) setProcessSummaryJob(job);
				} else setProcessSummaryJob(job);
			} catch (error) {
				if (active) console.error("[Themis] Erro ao consultar job V2:", error);
			} finally {
				pollInFlight = false;
			}
		};
		poll();
		const timer = setInterval(poll, 1200);
		return () => {
			active = false;
			clearInterval(timer);
		};
	}, [
		ctx,
		selectedPid,
		processSummaryJob?.job_id,
		processSummaryJob?.status
	]);
	useEffect(() => {
		if (selectedPid) ctx.storage.set("workspace.process.selectedId", selectedPid);
	}, [ctx, selectedPid]);
	useEffect(() => {
		setSummaryConfirmationMovement(null);
		setProcessSummaryConfirmation(null);
	}, [selectedPid]);
	useEffect(() => {
		setProcessSummaryJob(movementAnalysisJobFromStatus(summaryStatuses[selectedPid]));
	}, [selectedPid]);
	useEffect(() => {
		ctx.storage.set("workspace.process.view", activeSection);
	}, [ctx, activeSection]);
	useEffect(() => {
		if (pdfView?.processId && Number.isInteger(pdfView.pageNumber)) ctx.storage.set("workspace.pdf.current", {
			processId: pdfView.processId,
			pageNumber: pdfView.pageNumber
		});
	}, [ctx, pdfView]);
	useEffect(() => {
		const pages = autos[selectedPid]?.pages || [];
		if (activeSection !== "autos" || pages.length === 0) return void 0;
		const isNav = navTarget?.process_id === selectedPid && (navTarget.document_id || navTarget.pdf_page || navTarget.process_folio);
		let targetIndex = -1;
		if (isNav) targetIndex = pages.findIndex((p) => {
			const sref = p.source_ref || {};
			if (navTarget.document_id && sref.document_id === navTarget.document_id) {
				if (navTarget.pdf_page && Number(sref.pdf_page) === Number(navTarget.pdf_page)) return true;
				if (!navTarget.pdf_page) return true;
			}
			if (navTarget.pdf_page && Number(sref.pdf_page) === Number(navTarget.pdf_page)) return true;
			if (navTarget.process_folio && String(sref.process_folio) === String(navTarget.process_folio)) return true;
			return false;
		});
		const existingCount = visibleAutosPages[selectedPid] || 0;
		let initialCount = existingCount > 0 ? Math.min(pages.length, existingCount) : Math.min(pages.length, AUTOS_INITIAL_BATCH);
		if (targetIndex >= 0 && targetIndex >= initialCount) initialCount = Math.min(pages.length, targetIndex + 10);
		let cancelled = false;
		let frameId = null;
		let rendered = initialCount;
		setVisibleAutosPages((prev) => ({
			...prev,
			[selectedPid]: initialCount
		}));
		const renderNextBatch = () => {
			if (cancelled || rendered >= pages.length) return;
			frameId = requestAnimationFrame(() => {
				if (cancelled) return;
				rendered = Math.min(pages.length, rendered + AUTOS_RENDER_BATCH);
				setVisibleAutosPages((prev) => ({
					...prev,
					[selectedPid]: rendered
				}));
				renderNextBatch();
			});
		};
		renderNextBatch();
		return () => {
			cancelled = true;
			if (frameId !== null) cancelAnimationFrame(frameId);
		};
	}, [
		ctx,
		activeSection,
		selectedPid,
		autos,
		navTarget
	]);
	useEffect(() => {
		const pages = autos[selectedPid]?.pages || [];
		const rendered = visibleAutosPages[selectedPid] || 0;
		if (activeSection !== "autos" || rendered === 0 || pages.length === 0) return void 0;
		const savedReading = ctx.storage.get("workspace.autos.reading", {})[selectedPid];
		const isNav = navTarget?.process_id === selectedPid && (navTarget.document_id || navTarget.pdf_page);
		const targetKey = isNav ? Object.keys(autosPageRefs.current).find((k) => {
			if (navTarget.document_id && k.startsWith(navTarget.document_id)) {
				if (navTarget.pdf_page && k.endsWith(`:${navTarget.pdf_page}`)) return true;
			}
			if (navTarget.pdf_page && k.endsWith(`:${navTarget.pdf_page}`)) return true;
			return false;
		}) : savedReading?.pageKey;
		const pageElement = targetKey ? autosPageRefs.current[targetKey] : null;
		const restoreKey = `${selectedPid}:${targetKey || "start"}:${navTarget?.timestamp || ""}`;
		const frameId = requestAnimationFrame(() => {
			if (autosRestoreKeyRef.current === restoreKey || !autosScrollRef.current) return;
			if (targetKey && !pageElement) return;
			if (pageElement && autosScrollRef.current) {
				scrollContainerToElement(pageElement, autosScrollRef.current, isNav ? 0 : savedReading?.offset || 0);
				if (isNav) {
					pageElement.classList.add("ring-2", "ring-primary/70", "rounded-md", "transition-all");
					setTimeout(() => {
						pageElement.classList.remove("ring-2", "ring-primary/70");
					}, 2500);
				}
			} else if (!isNav) autosScrollRef.current.scrollTop = 0;
			autosRestoreKeyRef.current = restoreKey;
		});
		return () => cancelAnimationFrame(frameId);
	}, [
		ctx,
		activeSection,
		selectedPid,
		autos,
		visibleAutosPages,
		navTarget
	]);
	useEffect(() => {
		if (activeSection !== "pdf" || !selectedPid) return;
		if (pdfProcessIdRef.current === selectedPid && pdfBytesRef.current) return;
		if (processInFlightRef.current.pdf[selectedPid]) return;
		const processEntry = processes.find((process) => (process.process_id || process.id) === selectedPid);
		const processStatus = String(processEntry?.pipeline_status || processEntry?.status || "").toUpperCase();
		if (processStatus && !["READY", "ACTIVE"].includes(processStatus)) {
			setPdfLoading(false);
			setPdfError(null);
			return;
		}
		const pageNum = pdfView?.processId === selectedPid && pdfView?.pageNumber ? pdfView.pageNumber : 1;
		loadProcessPdf(selectedPid, pageNum);
	}, [
		activeSection,
		selectedPid,
		pdfView,
		processRefreshRevision
	]);
	useEffect(() => {
		if (navTarget?.section === "pdf" && (navTarget.process_id || selectedPid)) {
			const pid = navTarget.process_id || selectedPid;
			const pageNum = Number(navTarget.page_number || navTarget.integral_pdf_page || navTarget.process_folio || navTarget.process_page || navTarget.pdf_page || 1);
			openPdfAtPage(pageNum, pid);
			setActiveSection("pdf");
		}
	}, [navTarget]);
	useEffect(() => () => {
		pdfBytesRef.current = null;
		pdfProcessIdRef.current = "";
		const runtime = pdfJsRuntimeRef.current;
		if (runtime.style?.parentNode) runtime.style.parentNode.removeChild(runtime.style);
		if (runtime.workerUrl) URL.revokeObjectURL(runtime.workerUrl);
		pdfJsRuntimeRef.current = {
			promise: null,
			runtime: null,
			style: null
		};
	}, []);
	const filteredProcesses = useMemo(() => {
		return processes.filter((p) => {
			const pid = p.process_id || p.id || "";
			const label = p.label || "";
			if (!search) return true;
			const q = search.toLowerCase();
			return pid.toLowerCase().includes(q) || label.toLowerCase().includes(q);
		});
	}, [processes, search]);
	const handlePointerDown = (e) => {
		e.preventDefault();
		setIsDragging(true);
		const container = splitContainerRef.current;
		if (!container) return;
		const containerRect = container.getBoundingClientRect();
		const handlePointerMove = (moveEvent) => {
			const offsetX = moveEvent.clientX - containerRect.left;
			const totalWidth = containerRect.width;
			if (totalWidth <= 0) return;
			let newPct = offsetX / totalWidth * 100;
			const minPct = Math.max(18, 220 / totalWidth * 100);
			const maxPct = Math.min(72, (totalWidth - 280) / totalWidth * 100);
			newPct = Math.max(minPct, Math.min(maxPct, newPct));
			setListWidthPct(newPct);
		};
		const handlePointerUp = () => {
			setIsDragging(false);
			window.removeEventListener("pointermove", handlePointerMove);
			window.removeEventListener("pointerup", handlePointerUp);
		};
		window.addEventListener("pointermove", handlePointerMove);
		window.addEventListener("pointerup", handlePointerUp);
	};
	const handleDoubleClick = () => {
		setListWidthPct(30);
	};
	const saveAutosReading = () => {
		const container = autosScrollRef.current;
		if (!container || !selectedPid) return;
		const pageElements = Object.entries(autosPageRefs.current).filter(([, element]) => element).map(([key, element]) => [
			key,
			element,
			scrollOffsetWithinContainer(element, container)
		]).sort(([, , leftOffset], [, , rightOffset]) => leftOffset - rightOffset);
		const anchor = pageElements.reduce((best, entry) => entry[2] <= container.scrollTop + 8 ? entry : best, pageElements[0]);
		if (!anchor) return;
		const [pageKey, , elementOffset] = anchor;
		const allReadings = ctx.storage.get("workspace.autos.reading", {});
		ctx.storage.set("workspace.autos.reading", {
			...allReadings,
			[selectedPid]: {
				pageKey,
				offset: Math.max(0, container.scrollTop - elementOffset)
			}
		});
	};
	const handleAutosScroll = () => {
		if (autosScrollTimerRef.current) clearTimeout(autosScrollTimerRef.current);
		autosScrollTimerRef.current = setTimeout(saveAutosReading, 120);
	};
	const ensurePdfJsRuntime = () => {
		if (pdfJsRuntimeRef.current.promise) return pdfJsRuntimeRef.current.promise;
		pdfJsRuntimeRef.current.promise = loadPdfJsRuntime(ctx).then((runtime) => {
			const style = document.createElement("style");
			style.dataset.themisPdfjs = "true";
			style.textContent = runtime.cssText;
			document.head.appendChild(style);
			runtime.style = style;
			pdfJsRuntimeRef.current.runtime = runtime;
			pdfJsRuntimeRef.current.style = style;
			return runtime;
		});
		return pdfJsRuntimeRef.current.promise;
	};
	const loadProcessPdf = (processId, pageNumber = 1) => {
		if (!processId) return;
		const processEntry = processes.find((process) => (process.process_id || process.id) === processId);
		const processStatus = String(processEntry?.pipeline_status || processEntry?.status || "").toUpperCase();
		if (processStatus && !["READY", "ACTIVE"].includes(processStatus)) {
			setPdfLoading(false);
			setPdfError(null);
			return Promise.resolve(null);
		}
		const targetPage = Number(pageNumber) >= 1 ? Number(pageNumber) : 1;
		if (pdfProcessIdRef.current === processId && pdfBytesRef.current) {
			setPdfView((current) => ({
				...current,
				pageNumber: targetPage
			}));
			return;
		}
		if (processInFlightRef.current.pdf[processId]) return processInFlightRef.current.pdf[processId];
		setPdfLoading(true);
		setPdfError(null);
		const runtimePromise = ensurePdfJsRuntime();
		const request = ctx.rest(`/processes/${encodeURIComponent(processId)}/pdf`).then((data) => {
			if (!data?.content_base64) throw new Error("Conteúdo do PDF integral do processo indisponível");
			const bytes = decodeBase64Bytes(data.content_base64);
			return runtimePromise.then(() => bytes);
		}).then((bytes) => {
			if (selectedPidRef.current !== processId) return null;
			pdfBytesRef.current = bytes;
			pdfProcessIdRef.current = processId;
			setPdfData(bytes);
			setPdfView({
				processId,
				pageNumber: targetPage
			});
			setPdfLoading(false);
			return bytes;
		}).catch((err) => {
			console.error("[Themis] Erro ao carregar PDF integral do processo:", err);
			if (selectedPidRef.current === processId) {
				setPdfError(err.message || String(err));
				setPdfLoading(false);
			}
			return null;
		}).finally(() => {
			delete processInFlightRef.current.pdf[processId];
		});
		processInFlightRef.current.pdf[processId] = request;
		return request;
	};
	const openPdfAtPage = (pageNumber, processId = selectedPid) => {
		if (!processId) return;
		const targetPage = Number(pageNumber) >= 1 ? Number(pageNumber) : 1;
		saveAutosReading();
		autosRestoreKeyRef.current = "";
		if (pdfProcessIdRef.current === processId && pdfBytesRef.current) setPdfView((current) => ({
			...current,
			pageNumber: targetPage
		}));
		else {
			setPdfView((current) => ({
				...current,
				processId,
				pageNumber: targetPage
			}));
			loadProcessPdf(processId, targetPage);
		}
		setActiveSection("pdf");
	};
	pdfNavigationActionsRef.current = {
		saveAutosReading,
		openPdfAtPage
	};
	const registerAutosPageRef = useCallback((pageKey, element) => {
		if (element) autosPageRefs.current[pageKey] = element;
		else delete autosPageRefs.current[pageKey];
	}, []);
	const openPdfInside = useCallback((page) => {
		const processId = selectedPidRef.current;
		if (!processId) return;
		pdfNavigationActionsRef.current.saveAutosReading?.();
		autosRestoreKeyRef.current = "";
		const sourceRef = page?.source_ref || {};
		const pageNumber = Number(sourceRef.integral_pdf_page ?? page?.integral_pdf_page ?? sourceRef.process_folio ?? sourceRef.process_page_start ?? page?.process_page_number ?? sourceRef.process_page_number ?? sourceRef.pdf_page ?? page?.page ?? 1);
		pdfNavigationActionsRef.current.openPdfAtPage?.(pageNumber, processId);
	}, []);
	const openAutosAtMovementPage = (movement) => {
		const sourceRef = movement?.source_ref || {};
		const documentId = sourceRef.document_id;
		const pdfPage = Number(sourceRef.pdf_page);
		const processFolio = sourceRef.process_folio ?? sourceRef.process_page_start;
		if (!selectedPid || !documentId || !Number.isInteger(pdfPage) || pdfPage < 1 || processFolio == null) return;
		const readings = ctx.storage.get("workspace.autos.reading", {});
		ctx.storage.set("workspace.autos.reading", {
			...readings,
			[selectedPid]: {
				pageKey: `${documentId}:${pdfPage}`,
				offset: 0
			}
		});
		autosRestoreKeyRef.current = "";
		setActiveSection("autos");
	};
	const isMovementExpanded = (mov, idx) => {
		const key = mov.movement_id || String(idx);
		return Boolean(expandedMovements[selectedPid || "default"]?.[key]);
	};
	const toggleMovementExpanded = (mov, idx) => {
		const key = mov.movement_id || String(idx);
		const procKey = selectedPid || "default";
		setExpandedMovements((prev) => ({
			...prev,
			[procKey]: {
				...prev[procKey] || {},
				[key]: !prev[procKey]?.[key]
			}
		}));
	};
	const selectProcess = (pid) => {
		if (pid === selectedPid) return;
		if (activeSection === "autos") saveAutosReading();
		pdfBytesRef.current = null;
		pdfProcessIdRef.current = "";
		setPdfData(null);
		setPdfView(null);
		setPdfError(null);
		setPdfLoading(false);
		autosPageRefs.current = {};
		autosRestoreKeyRef.current = "";
		setVisibleAutosPages((prev) => ({
			...prev,
			[selectedPid]: 0,
			[pid]: AUTOS_INITIAL_BATCH
		}));
		setSelectedPid(pid);
	};
	const changeProcessSection = (section) => {
		if (section === "pesquisa" && pipelineRunning) return;
		if (activeSection === "autos") saveAutosReading();
		autosRestoreKeyRef.current = "";
		setActiveSection(section);
	};
	const generateMovementSummary = async (movement) => {
		const movementId = movement?.movement_id;
		if (!movementId || summaryLoading[movementId] || processSummaryBusyRef.current === selectedPid) return;
		const processId = selectedPid;
		const selectionEpoch = processSelectionRef.current.epoch;
		const isSelected = () => processSelectionMatches(processSelectionRef.current, processId, selectionEpoch);
		processSummaryBusyRef.current = processId;
		setSummaryLoading((previous) => ({
			...previous,
			[movementId]: true
		}));
		setSummaryErrors((previous) => ({
			...previous,
			[movementId]: null
		}));
		try {
			const modelSelection = await resolveAiModelForJob();
			let job = await ctx.rest(`/movements/${encodeURIComponent(movementId)}/summary`, {
				method: "POST",
				body: modelSelection
			});
			while (movementAnalysisJobIsActive(job)) {
				await new Promise((resolve) => setTimeout(resolve, 1e3));
				job = await ctx.rest(`/movements/${encodeURIComponent(movementId)}/summary/jobs/${encodeURIComponent(job.job_id)}`);
			}
			if (job?.status === "FAILED") throw new Error(job.error || "Falha desconhecida ao gerar resumo");
			const summaryValue = job?.summary || (job?.status === "COMPLETED" ? (await ctx.rest(`/movements/${encodeURIComponent(movementId)}/summary`))?.summary : null);
			if (job?.status !== "COMPLETED" || !summaryValue) throw new Error("O backend retornou um estado de resumo inválido");
			if (isSelected()) setMovementSummaries((previous) => ({
				...previous,
				[processId]: {
					...previous[processId] || {},
					[movementId]: summaryValue
				}
			}));
			const status = await ctx.rest(`/processes/${encodeURIComponent(processId)}/summaries/status`);
			if (isSelected()) {
				setSummaryStatuses((previous) => ({
					...previous,
					[processId]: status
				}));
				setExpandedMovementSummaries((previous) => ({
					...previous,
					[movementId]: true
				}));
			}
		} catch (error) {
			console.error("[Themis] Erro ao gerar resumo do movimento:", error);
			if (isSelected()) setSummaryErrors((previous) => ({
				...previous,
				[movementId]: movementSummaryErrorMessage(error)
			}));
		} finally {
			setSummaryLoading((previous) => ({
				...previous,
				[movementId]: false
			}));
			if (processSummaryBusyRef.current === processId) processSummaryBusyRef.current = false;
		}
	};
	const toggleMovementSummary = (movementId) => {
		if (!movementId) return;
		setExpandedMovementSummaries((previous) => ({
			...previous,
			[movementId]: !(previous[movementId] ?? true)
		}));
	};
	const requestMovementSummary = (movement) => {
		if (movementSummaries[selectedPid]?.[movement?.movement_id]) {
			setSummaryConfirmationMovement(movement);
			return;
		}
		generateMovementSummary(movement);
	};
	const generateProcessSummaries = async (forceAll = false) => {
		if (!selectedPid || !selectedSummaryStatusReady || processSummaryBusyRef.current === selectedPid || movementAnalysisJobIsActive(selectedSummaryJob)) return;
		const runProcessId = selectedPid;
		const selectionEpoch = processSelectionRef.current.epoch;
		const isSelected = () => processSelectionMatches(processSelectionRef.current, runProcessId, selectionEpoch);
		processSummaryBusyRef.current = runProcessId;
		setProcessSummaryJob({
			process_id: runProcessId,
			status: "PENDING",
			total: summaryStatuses[runProcessId]?.v2_pending || 0,
			total_eligible: summaryStatuses[runProcessId]?.total_eligible || 0,
			completed: 0,
			failed: 0,
			pending: summaryStatuses[runProcessId]?.v2_pending || 0,
			errors: []
		});
		setSummaryErrors((previous) => ({
			...previous,
			[`__process__:${runProcessId}`]: null
		}));
		try {
			const modelSelection = await resolveAiModelForJob();
			let job = await ctx.rest(`/processes/${encodeURIComponent(runProcessId)}/summaries`, {
				method: "POST",
				body: {
					...modelSelection,
					force_all: forceAll
				}
			});
			if (isSelected()) setProcessSummaryJob(job);
			if (!movementAnalysisJobIsActive(job) && ![
				"COMPLETED",
				"PARTIAL",
				"FAILED"
			].includes(String(job?.status || "").toUpperCase())) throw new Error("O backend retornou um estado de job inválido");
		} catch (error) {
			console.error("[Themis] Erro ao gerar resumos do processo:", error);
			if (isSelected()) {
				setSummaryErrors((previous) => ({
					...previous,
					[`__process__:${runProcessId}`]: movementSummaryErrorMessage(error)
				}));
				setProcessSummaryJob((previous) => ({
					...previous || {},
					process_id: runProcessId,
					status: "FAILED",
					error: movementSummaryErrorMessage(error),
					completed_at: (/* @__PURE__ */ new Date()).toISOString()
				}));
			}
		} finally {
			if (processSummaryBusyRef.current === runProcessId) processSummaryBusyRef.current = false;
		}
	};
	const generateCaseSynthesis = async () => {
		if (!selectedPid || ["PENDING", "RUNNING"].includes(String(caseSynthesisJobs[selectedPid]?.status || "").toUpperCase())) return;
		const processId = selectedPid;
		setSummaryErrors((previous) => ({
			...previous,
			[`__case__:${processId}`]: null
		}));
		setCaseSynthesisJobs((previous) => ({
			...previous,
			[processId]: {
				process_id: processId,
				status: "PENDING"
			}
		}));
		try {
			const modelSelection = await resolveAiModelForJob();
			const job = await ctx.rest(`/processes/${encodeURIComponent(processId)}/case-synthesis`, {
				method: "POST",
				body: modelSelection
			});
			if (selectedPidRef.current === processId) setCaseSynthesisJobs((previous) => ({
				...previous,
				[processId]: job
			}));
		} catch (error) {
			console.error("[Themis] Erro ao gerar síntese do caso:", error);
			setSummaryErrors((previous) => ({
				...previous,
				[`__case__:${processId}`]: movementSummaryErrorMessage(error)
			}));
			setCaseSynthesisJobs((previous) => ({
				...previous,
				[processId]: null
			}));
		}
	};
	const requestAllProcessSummaries = () => {
		const status = summaryStatuses[selectedPid];
		if (!selectedSummaryStatusReady || !status || processSummaryBusyRef.current === selectedPid || movementAnalysisJobIsActive(selectedSummaryJob)) return;
		setProcessSummaryConfirmation({ count: status.total_eligible || status.total || 0 });
	};
	const currentOverview = overviews[selectedPid] || null;
	const currentMovements = movements[selectedPid] || [];
	const currentProcess = processes.find((process) => (process.process_id || process.id) === selectedPid) || null;
	const selectedSummaryStatus = summaryStatuses[selectedPid] || null;
	const selectedSummaryJob = processSummaryJob?.process_id === selectedPid ? processSummaryJob : movementAnalysisJobFromStatus(selectedSummaryStatus);
	const selectedSummaryJobStatus = String(selectedSummaryJob?.status || "").toUpperCase();
	const selectedSummaryJobActive = movementAnalysisJobIsActive(selectedSummaryJob);
	const selectedSummaryStatusReady = summaryStatusReady?.pid === selectedPid && summaryStatusReady.epoch === processSelectionRef.current.epoch;
	const v2EligibleTotal = Number(selectedSummaryStatus?.total_eligible ?? selectedSummaryJob?.total_eligible ?? selectedSummaryJob?.total ?? 0);
	const v2PendingTotal = Number(selectedSummaryStatus?.v2_pending ?? selectedSummaryJob?.pending ?? 0);
	const summaryJobMessage = movementAnalysisJobMessage(selectedSummaryJob);
	const pipelineStatus = String(currentProcess?.pipeline_status || "").toUpperCase();
	const pipelineRunning = [
		"CAPTURED",
		"QUEUED",
		"PROCESSING",
		"INGESTING",
		"VALIDATED",
		"EXTRACTING",
		"STRUCTURING",
		"INDEXING",
		"FINALIZING"
	].includes(pipelineStatus);
	const pipelineProgress = currentProcess?.pipeline_progress || {};
	const pipelinePercent = Math.max(0, Math.min(100, Number(pipelineProgress.percentage) || 0));
	const currentAutos = autos[selectedPid] || null;
	const renderedAutosCount = activeSection === "autos" && currentAutos?.pages?.length > 0 ? Math.min(currentAutos.pages.length, visibleAutosPages[selectedPid] || AUTOS_INITIAL_BATCH) : 0;
	return jsxs("main", {
		className: "flex min-h-0 flex-1 flex-col overflow-hidden p-4 sm:p-5 gap-3",
		children: [
			jsx("style", { children: MARKDOWN_DOCUMENT_CSS }),
			pipelineRunning || pipelineStatus === "ERROR" ? jsxs("div", {
				role: pipelineStatus === "ERROR" ? "alert" : "status",
				className: cn("order-last shrink-0 rounded-md border px-3 py-2", pipelineStatus === "ERROR" ? "border-destructive/30 bg-destructive/5 text-destructive" : "border-primary/20 bg-primary/5 text-foreground"),
				children: [
					jsxs("div", {
						className: "flex items-center justify-between gap-3 text-xs font-medium",
						children: [jsx("span", { children: pipelineStatus === "ERROR" ? "Falha ao processar o processo" : "Themis está processando este processo" }), pipelineStatus === "ERROR" ? null : jsx("span", {
							className: "tabular-nums text-muted-foreground",
							children: `${pipelinePercent}%`
						})]
					}),
					jsx("p", {
						className: "mt-1 text-[0.6875rem] text-muted-foreground",
						children: pipelineStatus === "ERROR" ? currentProcess?.pipeline_error || pipelineProgress.error || "Ocorreu um erro durante o processamento." : pipelineProgress.message || `Etapa: ${pipelineProgress.phase || pipelineStatus}`
					}),
					pipelineStatus === "ERROR" ? null : jsx("div", {
						className: "mt-2 h-1 overflow-hidden rounded-full bg-muted",
						role: "progressbar",
						"aria-label": "Progresso do processamento no Themis",
						"aria-valuemin": 0,
						"aria-valuemax": 100,
						"aria-valuenow": pipelinePercent,
						children: jsx("div", {
							className: "h-full rounded-full bg-primary transition-[width] duration-300",
							style: { width: `${pipelinePercent}%` }
						})
					})
				]
			}) : null,
			jsx(ConfirmDialog, {
				open: Boolean(summaryConfirmationMovement),
				onClose: () => setSummaryConfirmationMovement(null),
				onConfirm: async () => {
					if (summaryConfirmationMovement) await generateMovementSummary(summaryConfirmationMovement);
					setSummaryConfirmationMovement(null);
				},
				title: "Atualizar resumo do ato?",
				description: "Uma nova versão será gerada. O resumo atual permanecerá preservado no histórico.",
				confirmLabel: "Gerar nova versão",
				cancelLabel: "Cancelar",
				busyLabel: "Gerando...",
				doneLabel: "Gerado"
			}),
			jsx(ConfirmDialog, {
				open: Boolean(processSummaryConfirmation),
				onClose: () => setProcessSummaryConfirmation(null),
				onConfirm: async () => {
					await generateProcessSummaries(true);
					setProcessSummaryConfirmation(null);
				},
				title: "Atualizar todos os resumos?",
				description: processSummaryConfirmation ? `Serão geradas ${processSummaryConfirmation.count} novas versões. As versões atuais serão preservadas no histórico.` : null,
				confirmLabel: "Atualizar todos",
				cancelLabel: "Cancelar",
				busyLabel: "Gerando...",
				doneLabel: "Gerados"
			}),
			jsxs("div", {
				className: "flex items-start justify-between gap-3",
				children: [jsx(PanelHeader, {
					title: "Gestão Processual",
					subtitle: `Acervo de processos judiciais indexados (${filteredProcesses.length})`
				}), jsxs("div", {
					className: "flex items-center gap-2 shrink-0",
					children: [jsxs(DropdownMenu, {
						open: modelMenuOpen,
						onOpenChange: setModelMenuOpen,
						children: [jsx(DropdownMenuTrigger, {
							asChild: true,
							children: jsxs(Button, {
								variant: "outline",
								className: "h-7 max-w-[22rem] min-w-[13rem] justify-between gap-2 px-2.5 text-xs font-normal",
								"aria-label": "Modelo das operações de IA da Themis",
								children: [jsx("span", {
									className: "min-w-0 truncate",
									children: modelTriggerLabel
								}), jsx(Codicon, {
									name: "chevron-down",
									size: "0.7rem",
									className: "shrink-0 opacity-50"
								})]
							})
						}), jsx(DropdownMenuContent, {
							align: "end",
							className: "w-72 p-0",
							children: jsx(ModelMenuCloseContext.Provider, {
								value: () => setModelMenuOpen(false),
								children: jsx(ModelCatalogMenu, { controller: modelMenuController })
							})
						})]
					})]
				})]
			}),
			jsxs("div", {
				ref: splitContainerRef,
				className: cn("flex min-h-0 flex-1 flex-row overflow-hidden", isDragging && "select-none"),
				children: [
					jsx("div", {
						style: {
							flex: `0 0 ${listWidthPct}%`,
							width: `${listWidthPct}%`,
							minWidth: "220px",
							maxWidth: "calc(100% - 280px)"
						},
						className: "flex min-h-0 min-w-0 flex-col overflow-hidden pr-1",
						children: jsx(PanelList, {
							className: "w-full min-[47.5rem]:w-full min-w-0 flex-1 h-full min-h-0 max-w-none [&_input]:w-full [&_input]:min-w-0 [&_input]:flex-1",
							searchValue: search,
							onSearchChange: setSearch,
							searchPlaceholder: "Buscar por CNJ...",
							children: loading ? jsx("div", {
								className: "p-4 text-center text-xs text-muted-foreground",
								children: "Carregando acervo processual..."
							}) : error ? jsxs("div", {
								className: "p-4 text-center text-xs text-destructive space-y-1",
								children: [jsx("div", {
									className: "font-semibold",
									children: "Falha ao carregar processos"
								}), jsx("div", {
									className: "text-[0.6875rem] text-muted-foreground",
									children: error
								})]
							}) : filteredProcesses.length === 0 ? jsx("div", {
								className: "p-4 text-center text-xs text-muted-foreground",
								children: "Nenhum processo correspondente"
							}) : jsx("div", {
								className: "flex flex-col gap-1 p-1",
								children: filteredProcesses.map((proc) => {
									const pid = proc.process_id || proc.id;
									return jsxs(PanelListRow, {
										active: pid === selectedPid,
										icon: "folder",
										onSelect: () => selectProcess(pid),
										rowKey: pid,
										title: jsxs("span", {
											className: "flex min-w-0 flex-col gap-0.5",
											children: [jsx("span", {
												className: "truncate font-mono text-xs font-semibold",
												children: pid
											}), proc.label ? jsx("span", {
												className: "truncate text-[0.68rem] font-normal text-muted-foreground",
												children: proc.label
											}) : null]
										})
									}, pid);
								})
							})
						})
					}),
					jsxs("div", {
						role: "separator",
						"aria-orientation": "vertical",
						"aria-valuenow": Math.round(listWidthPct),
						onPointerDown: handlePointerDown,
						onDoubleClick: handleDoubleClick,
						className: cn("group relative flex w-2.5 shrink-0 cursor-col-resize select-none items-center justify-center transition-colors", isDragging && "cursor-col-resize"),
						style: { touchAction: "none" },
						title: "Arraste para redimensionar (duplo clique para restaurar)",
						children: [jsx("div", { className: cn("h-full w-px bg-border/40 transition-all duration-150", "group-hover:w-0.5 group-hover:bg-primary/50", isDragging && "w-0.5 bg-primary") })]
					}),
					jsx("div", {
						style: {
							flex: "1 1 0%",
							minWidth: "280px"
						},
						className: "flex min-h-0 min-w-0 flex-col overflow-hidden pl-2",
						children: selectedPid ? jsxs("div", {
							className: "flex min-h-0 flex-1 flex-col overflow-hidden",
							children: [jsxs("div", {
								className: "flex flex-wrap items-center justify-between gap-3 border-b border-border/40 pb-3 mb-3",
								children: [jsxs("div", {
									className: "min-w-0 space-y-0.5",
									children: [jsx("span", {
										className: "text-[0.6875rem] font-semibold text-muted-foreground uppercase tracking-wider",
										children: "Processo Judicial Eletrônico"
									}), jsx("h2", {
										className: "font-mono text-base font-bold text-foreground truncate",
										children: selectedPid
									})]
								}), jsx(SegmentedControl, {
									options: pipelineRunning ? PROCESS_SECTIONS.map((option) => option.id === "pesquisa" ? {
										...option,
										label: "Pesquisa · indexando"
									} : option) : PROCESS_SECTIONS,
									value: activeSection,
									onChange: changeProcessSection
								})]
							}), jsxs(React.Fragment, { children: [
								jsxs("div", {
									className: activeSection === "dossie" ? "contents" : "hidden",
									children: [jsxs(PanelDetail, {
										className: "themis-scroll-visible min-h-0 flex-1 overflow-y-auto overscroll-contain pr-1 space-y-4",
										"data-themis-page-scroll": "true",
										children: [currentOverview ? jsxs(React.Fragment, { children: [
											jsx(PanelSectionLabel, { children: "Informações Cadastrais / Capa CPOPG" }),
											(() => {
												const metaData = currentOverview.metadata || {};
												const basicData = metaData.provenance?.basic_data || {};
												const metaRows = [
													{
														label: "Processo (CNJ)",
														value: currentOverview.process_id
													},
													metaData.classe || basicData.classe ? {
														label: "Classe",
														value: metaData.classe || basicData.classe
													} : null,
													metaData.assunto || basicData.assunto ? {
														label: "Assunto",
														value: metaData.assunto || basicData.assunto
													} : null,
													basicData.outros_assuntos ? {
														label: "Outros Assuntos",
														value: basicData.outros_assuntos
													} : null,
													metaData.comarca || basicData.foro ? {
														label: "Foro / Comarca",
														value: metaData.comarca || basicData.foro
													} : null,
													metaData.unidade || basicData.vara ? {
														label: "Vara",
														value: metaData.unidade || basicData.vara
													} : null,
													basicData.juiz ? {
														label: "Juiz",
														value: basicData.juiz
													} : null,
													basicData.distribuicao ? {
														label: "Distribuição",
														value: basicData.distribuicao
													} : null,
													basicData.controle ? {
														label: "Controle",
														value: basicData.controle
													} : null,
													basicData.area ? {
														label: "Área",
														value: basicData.area
													} : null,
													basicData.valor_acao ? {
														label: "Valor da Ação",
														value: basicData.valor_acao
													} : null,
													basicData.segredo_justica !== void 0 ? {
														label: "Segredo de Justiça",
														value: basicData.segredo_justica ? "Sim" : "Não"
													} : null,
													{
														label: "Status / Situação",
														value: currentOverview.status || "Ativo"
													},
													{
														label: "Autos",
														value: `${currentOverview.total_pages || 0} páginas indexadas (${currentOverview.document_count || 0} peças)`
													}
												].filter(Boolean);
												return jsx("div", {
													className: "space-y-1 text-[0.7rem]",
													children: metaRows.map((row, index) => jsxs("div", {
														className: "grid items-baseline gap-x-2",
														style: { gridTemplateColumns: "14rem minmax(0, 1fr)" },
														children: [jsx("span", {
															className: "truncate text-muted-foreground/55",
															children: row.label
														}), jsx("span", {
															className: "min-w-0 break-words text-foreground/85",
															children: row.value
														})]
													}, `${row.label}-${index}`))
												});
											})(),
											currentOverview.hearings && currentOverview.hearings.length > 0 ? jsxs(React.Fragment, { children: [jsx(PanelSectionLabel, { children: `Audiências Designadas (${currentOverview.hearings.length})` }), jsx("div", {
												className: "space-y-2",
												children: currentOverview.hearings.map((h, idx) => {
													const hStatus = (h.status || "").toUpperCase();
													const hTone = hStatus.includes("CANCEL") ? "bad" : hStatus.includes("REDESIGN") ? "warn" : "good";
													const hDate = formatDateDisplay(h.scheduled_at);
													const hTime = formatTimeDisplay(h.scheduled_at, h.date_precision);
													const hDateStr = hTime ? `${hDate} às ${hTime}` : hDate;
													return jsxs("div", {
														className: "rounded-md border border-border/40 bg-card/60 p-3 text-xs space-y-1.5",
														children: [jsxs("div", {
															className: "flex items-center justify-between gap-2",
															children: [jsx("span", {
																className: "font-semibold text-foreground",
																children: h.hearing_type || "Audiência"
															}), jsx(PanelPill, {
																tone: hTone,
																children: h.status || "Designada"
															})]
														}), jsxs("div", {
															className: "text-muted-foreground text-xs space-y-0.5",
															children: [
																jsxs("div", { children: [jsx("strong", {
																	className: "text-foreground/80 font-medium",
																	children: "Data/Hora: "
																}), hDateStr] }),
																h.location && h.location !== "None" ? jsxs("div", { children: [jsx("strong", {
																	className: "text-foreground/80 font-medium",
																	children: "Local/Sala: "
																}), h.location] }) : null,
																h.outcome_notes && h.outcome_notes !== h.status ? jsxs("div", { children: [jsx("strong", {
																	className: "text-foreground/80 font-medium",
																	children: "Observações: "
																}), h.outcome_notes] }) : null
															]
														})]
													}, h.hearing_id || idx);
												})
											})] }) : null,
											jsx(PanelSectionLabel, { children: "Identificação & Qualificação das Partes" }),
											currentOverview.participants && currentOverview.participants.length > 0 ? jsx("div", {
												className: "space-y-2",
												children: currentOverview.participants.map((p, idx) => {
													const roleUpper = (p.role || "PARTE").toUpperCase();
													const roleRawUpper = (p.role_raw || "").toUpperCase();
													const additionalRoleUppers = (p.additional_roles || []).map((role) => String(role).toUpperCase());
													const isLawyer = roleUpper === "ADVOGADO" || roleUpper === "ADVOGADA" || roleUpper === "LAWYER" || roleRawUpper.startsWith("ADVOGAD") || additionalRoleUppers.some((role) => role.startsWith("ADVOGAD") || role === "LAWYER");
													const isAutor = roleUpper.includes("AUTOR") || roleUpper.includes("REQUERENTE");
													const isReu = roleUpper.includes("REU") || roleUpper.includes("REQUERIDO");
													const tone = isAutor ? "good" : isReu ? "warn" : "muted";
													const idList = [];
													if (p.identifiers?.CPF) idList.push(`CPF: ${p.identifiers.CPF}`);
													if (p.identifiers?.CNPJ) idList.push(`CNPJ: ${p.identifiers.CNPJ}`);
													if (p.identifiers?.OAB) idList.push(`OAB: ${p.identifiers.OAB}`);
													if (p.identifiers?.RG) idList.push(`RG: ${p.identifiers.RG}`);
													return jsxs("div", {
														className: cn("rounded-md border border-border/40 bg-card/60 p-3 text-xs space-y-1", isLawyer && "ml-5 border-l-2 border-l-muted-foreground/30"),
														children: [
															jsxs("div", {
																className: "flex items-center justify-between gap-2",
																children: [jsx("span", {
																	className: "font-semibold text-foreground",
																	children: p.display_name
																}), jsxs("div", {
																	className: "flex flex-wrap justify-end gap-1",
																	children: [jsx(PanelPill, {
																		tone,
																		children: p.role || "Parte"
																	}), ...(p.additional_roles || []).map((role, roleIdx) => jsx(PanelPill, {
																		tone: "muted",
																		children: role
																	}, `${p.entity_id || p.display_name || "participant"}:role:${roleIdx}`))]
																})]
															}),
															idList.length > 0 ? jsx("div", {
																className: "text-muted-foreground font-mono text-[0.68rem]",
																children: idList.join(" · ")
															}) : null,
															p.represented_parties && p.represented_parties.length > 0 ? jsx("div", {
																className: "text-muted-foreground text-[0.68rem]",
																children: `Representa: ${p.represented_parties.join(", ")}`
															}) : null
														]
													}, `${p.entity_id || p.display_name || "participant"}:${roleRawUpper || roleUpper}:${idx}`);
												})
											}) : jsx("div", {
												className: "text-xs text-muted-foreground italic",
												children: "Nenhuma parte qualificada vinculada diretamente."
											}),
											jsx(PanelSectionLabel, { children: "Síntese do Caso" }),
											(() => {
												const caseData = caseSyntheses[selectedPid];
												const caseJob = caseSynthesisJobs[selectedPid];
												const synthesis = caseData?.synthesis;
												const caseJobActive = ["PENDING", "RUNNING"].includes(String(caseJob?.status || "").toUpperCase());
												const status = caseJobActive ? "RUNNING" : caseData?.status;
												const action = status === "MISSING" ? {
													label: "Gerar síntese",
													icon: "sparkle"
												} : status === "STALE" || status === "CURRENT" ? {
													label: "Atualizar síntese",
													icon: "edit"
												} : null;
												return jsxs("div", {
													className: "space-y-2",
													children: [
														jsxs("div", {
															className: "flex items-center justify-between gap-2",
															children: [jsx("span", {
																className: "text-[0.68rem] text-muted-foreground",
																children: status === "CURRENT" ? "Síntese atualizada" : status === "STALE" ? "Síntese desatualizada" : status === "RUNNING" ? "Gerando síntese..." : status === "MISSING" ? "Síntese ainda não gerada" : "Carregando síntese..."
															}), action ? jsx(PanelAction, {
																icon: action.icon,
																disabled: caseJobActive,
																onClick: generateCaseSynthesis,
																children: action.label
															}) : null]
														}),
														synthesis ? jsxs("div", {
															className: "space-y-3",
															children: [
																jsx("div", {
																	className: "text-[0.68rem] text-muted-foreground/70",
																	children: [
																		synthesis.provider,
																		synthesis.model,
																		synthesis.generated_at
																	].filter(Boolean).join(" · ")
																}),
																jsx(MessageTextContent, {
																	text: caseSynthesisDisplayMarkdown(synthesis.case_synthesis),
																	media: false
																}),
																synthesis.current_status ? jsxs("div", {
																	className: "space-y-1",
																	children: [jsx(PanelSectionLabel, { children: "Situação Atual" }), jsx(MessageTextContent, {
																		text: synthesis.current_status,
																		media: false
																	})]
																}) : null,
																synthesis.pending_issues?.length > 0 ? jsxs("div", {
																	className: "space-y-1",
																	children: [jsx(PanelSectionLabel, { children: "Questões Pendentes" }), jsx("ul", {
																		className: "list-disc space-y-1 pl-5 text-xs text-muted-foreground",
																		children: synthesis.pending_issues.map((item, idx) => jsx("li", { children: item.text }, `${idx}-${item.text}`))
																	})]
																}) : null
															]
														}) : null,
														summaryErrors[`__case__:${selectedPid}`] ? jsx("div", {
															className: "text-xs text-destructive",
															children: summaryErrors[`__case__:${selectedPid}`]
														}) : null
													]
												});
											})(),
											currentOverview.strategy_items && currentOverview.strategy_items.length > 0 ? jsx("div", {
												className: "space-y-2",
												children: currentOverview.strategy_items.map((strat, idx) => {
													return jsxs("div", {
														className: "rounded-md border border-border/40 bg-muted/20 p-3 text-xs space-y-1",
														children: [jsx("div", {
															className: "font-semibold text-foreground",
															children: strat.title
														}), jsx(PanelBlock, { children: strat.content })]
													}, strat.strategy_id || idx);
												})
											}) : jsx("div", {
												className: "text-xs text-muted-foreground italic",
												children: "Nenhuma síntese ou estratégia cadastrada."
											}),
											jsx(PanelSectionLabel, { children: "Diligências e Pendências" }),
											currentOverview.pending_items && currentOverview.pending_items.length > 0 ? jsx("div", {
												className: "space-y-2",
												children: currentOverview.pending_items.map((pend, idx) => {
													const isHigh = pend.priority === "HIGH" || pend.priority === "ALTA";
													return jsxs("div", {
														className: "rounded-md border border-border/40 bg-card/60 p-3 text-xs space-y-1",
														children: [jsxs("div", {
															className: "flex items-center justify-between gap-2",
															children: [jsx("span", {
																className: "font-semibold text-foreground",
																children: pend.title
															}), jsx(PanelPill, {
																tone: isHigh ? "bad" : "muted",
																children: isHigh ? "Prioridade Alta" : "Normal"
															})]
														}), pend.description ? jsx("div", {
															className: "text-muted-foreground text-xs leading-relaxed",
															children: pend.description
														}) : null]
													}, pend.pending_id || idx);
												})
											}) : jsx("div", {
												className: "text-xs text-muted-foreground italic",
												children: "Nenhuma pendência ativa registrada."
											})
										] }) : jsx(PanelEmpty, {
											icon: "inbox",
											title: "Resumo em preparação",
											description: "Metadados cadastrais do processo não disponíveis no momento."
										})]
									})]
								}),
								jsxs("div", {
									className: activeSection === "timeline" ? "flex min-h-0 flex-1 flex-col overflow-hidden" : "hidden",
									children: [jsxs("div", {
										className: "themis-scroll-visible min-h-0 h-0 flex-1 overflow-y-auto overscroll-contain pr-1 space-y-2",
										"data-themis-page-scroll": "true",
										children: [jsxs("div", {
											className: "flex items-center justify-between gap-2",
											children: [jsx(PanelSectionLabel, { children: `Movimentos Processuais (${currentMovements.length})` }), jsxs("div", {
												className: "flex flex-col items-end gap-1",
												children: [jsxs("div", {
													className: "flex items-center gap-2",
													children: [
														jsx("span", {
															className: "text-[0.68rem] text-muted-foreground",
															children: selectedSummaryStatusReady ? `${selectedSummaryStatus?.v2_completed ?? 0}/${v2EligibleTotal} resumos · ${v2PendingTotal} pendentes` : summaryStatusError?.pid === selectedPid && summaryStatusError.epoch === processSelectionRef.current.epoch ? "Falha ao carregar estado dos resumos" : "Carregando estado dos resumos…"
														}),
														jsx(PanelAction, {
															icon: selectedSummaryJobActive ? "loading~spin" : v2PendingTotal > 0 ? "sparkle" : "edit",
															disabled: !selectedSummaryStatusReady || selectedSummaryJobActive || v2PendingTotal === 0,
															onClick: () => generateProcessSummaries(false),
															children: selectedSummaryJobActive ? "Gerando resumos..." : !selectedSummaryStatusReady ? "Gerar resumos V2" : selectedSummaryJobStatus === "PARTIAL" || selectedSummaryJobStatus === "FAILED" ? `Continuar (${v2PendingTotal} pendentes)` : `Gerar ${v2PendingTotal} resumos V2`
														}),
														jsx(PanelAction, {
															icon: "edit",
															disabled: !selectedSummaryStatusReady || pipelineRunning || selectedSummaryJobActive || v2EligibleTotal === 0,
															onClick: requestAllProcessSummaries,
															children: "Atualizar todos"
														})
													]
												}), summaryJobMessage ? jsx("div", {
													className: `max-w-[48rem] text-right text-[0.68rem] ${selectedSummaryJobStatus === "PARTIAL" || selectedSummaryJobStatus === "FAILED" ? "text-destructive" : "text-muted-foreground"}`,
													role: "status",
													"aria-live": "polite",
													children: summaryJobMessage
												}) : null]
											})]
										}), currentMovements.length === 0 ? jsx(PanelEmpty, {
											icon: pipelineRunning ? "clock" : pipelineStatus === "ERROR" ? "error" : "clock",
											title: pipelineRunning ? "Sincronização em andamento" : pipelineStatus === "ERROR" ? "Falha na sincronização" : "Nenhuma movimentação",
											description: pipelineRunning ? currentProcess?.pipeline_progress?.message || "Os documentos estão sendo recebidos e processados. As movimentações aparecerão ao término da sincronização." : pipelineStatus === "ERROR" ? currentProcess?.pipeline_error || "O processamento dos documentos falhou. Tente sincronizar novamente após corrigir o problema." : "Não foram encontradas movimentações processuais no histórico."
										}) : currentMovements.map((mov, idx) => renderMovementItem(mov, idx, openAutosAtMovementPage, isMovementExpanded(mov, idx), () => toggleMovementExpanded(mov, idx), movementSummaries[selectedPid]?.[mov.movement_id] || null, Boolean(summaryLoading[mov.movement_id]), summaryErrors[mov.movement_id] || null, () => requestMovementSummary(mov), expandedMovementSummaries[mov.movement_id] ?? true, () => toggleMovementSummary(mov.movement_id), processSummaryJob?.process_id === selectedPid && processSummaryJob?.status === "RUNNING"))]
									})]
								}),
								jsxs("div", {
									className: activeSection === "pesquisa" ? "contents" : "hidden",
									children: [pipelineRunning ? jsx(PanelEmpty, {
										icon: "clock",
										title: "Pesquisa disponível após a indexação",
										description: pipelineProgress.message || "O índice de pesquisa deste processo ainda está sendo preparado."
									}) : jsx(PesquisaView, {
										key: selectedPid,
										ctx,
										processId: selectedPid,
										onNavigateAutos,
										onNavigatePdf
									})]
								}),
								jsxs("div", {
									className: activeSection === "autos" || activeSection === "pdf" ? "contents" : "hidden",
									children: [jsxs("div", {
										className: "min-h-0 flex-1 flex flex-col",
										children: [jsxs("div", {
											className: activeSection === "autos" ? "contents" : "hidden",
											children: [jsxs("div", {
												ref: autosScrollRef,
												onScroll: handleAutosScroll,
												className: "themis-scroll-visible min-h-0 flex-1 overflow-y-auto overscroll-contain px-2 py-1",
												"data-themis-page-scroll": "true",
												"data-autos-rendered-pages": renderedAutosCount,
												"data-autos-total-pages": currentAutos?.pages?.length || 0,
												children: [!currentAutos?.pages || currentAutos.pages.length === 0 ? jsx(PanelEmpty, {
													icon: "book",
													title: "Autos não indexados",
													description: "As páginas digitalizadas deste processo ainda não foram processadas."
												}) : jsx("div", {
													className: "space-y-6",
													style: {
														width: "46rem",
														maxWidth: "calc(100% - 2rem)",
														marginInline: "auto"
													},
													children: currentAutos.pages.slice(0, renderedAutosCount).map((page, idx) => jsx(AutosPageItem, {
														page,
														idx,
														onOpenPdfInside: openPdfInside,
														registerPageRef: registerAutosPageRef
													}, `page-${page.document_id || ""}-${page.page || idx}`))
												})]
											})]
										}), jsxs("div", {
											className: activeSection === "pdf" ? "relative flex min-h-0 flex-1 flex-col overflow-hidden" : "hidden",
											children: [pdfLoading ? jsx("div", {
												className: "flex min-h-0 flex-1 items-center justify-center text-xs text-muted-foreground",
												children: "Carregando PDF original..."
											}) : pdfError ? jsx(PanelEmpty, {
												icon: "warning",
												title: "PDF indisponível",
												description: pdfError
											}) : pipelineRunning ? jsx(PanelEmpty, {
												icon: "clock",
												title: "PDF disponível após o processamento",
												description: pipelineProgress.message || "O Themis está preparando os documentos deste processo."
											}) : pipelineStatus === "ERROR" ? jsx(PanelEmpty, {
												icon: "warning",
												title: "PDF indisponível",
												description: currentProcess?.pipeline_error || pipelineProgress.error || "O processamento do processo falhou."
											}) : pdfData && pdfProcessIdRef.current === selectedPid ? jsx(PdfJsViewer, {
												pdfData,
												runtimePromise: pdfJsRuntimeRef.current.promise,
												pageNumber: pdfView?.pageNumber || 1,
												active: activeSection === "pdf",
												onPageChange: (pageNumber) => {
													setPdfView((current) => current ? {
														...current,
														pageNumber
													} : current);
												},
												onError: (error) => {
													console.error("[Themis] Erro no viewer PDF.js:", error);
													if (selectedPidRef.current === selectedPid) {
														setPdfError(error?.message || String(error));
														setPdfLoading(false);
													}
												}
											}) : jsx(PanelEmpty, {
												icon: "book",
												title: "Nenhum PDF carregado",
												description: "O PDF integral do processo será carregado ao selecionar a visão PDF."
											})]
										})]
									})]
								})
							] })]
						}) : jsx(PanelEmpty, {
							icon: "folder",
							title: "Nenhum processo selecionado",
							description: "Selecione um processo na lista à esquerda para visualizar seu dossiê e autos."
						})
					})
				]
			})
		]
	});
}
function PesquisaView({ ctx, processId, onNavigateAutos, onNavigatePdf }) {
	const selectedPid = processId;
	const [query, setQuery] = useState("");
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState(null);
	const [resultState, setResult] = useState(null);
	const [searchMode, setSearchMode] = useState("rag");
	const textareaRef = useRef(null);
	const selectedPidRef = useRef(selectedPid);
	selectedPidRef.current = selectedPid;
	const requestSequenceRef = useRef(0);
	const warmupRequestedRef = useRef(false);
	const triggerWarmupIfValid = (text) => {
		if (warmupRequestedRef.current) return;
		if ((text || "").trim().length > 0) {
			warmupRequestedRef.current = true;
			ctx.rest("/embedding/warmup", { method: "POST" }).catch(() => {});
		}
	};
	useEffect(() => {
		if (!query.trim()) warmupRequestedRef.current = false;
	}, [query]);
	const result = resultState?.process_id === selectedPid ? resultState.value : null;
	useEffect(() => () => {
		requestSequenceRef.current += 1;
	}, []);
	const executeSearch = async (queryText = query, mode = searchMode) => {
		const q = (queryText || "").trim();
		if (!q) return;
		if (!selectedPid) {
			setError("Selecione um processo antes de pesquisar.");
			return;
		}
		const requestId = ++requestSequenceRef.current;
		const requestProcessId = selectedPid;
		setLoading(true);
		setError(null);
		try {
			const endpoint = mode === "rag" ? "/retrieval/answer" : "/retrieval/search";
			const res = await ctx.rest(endpoint, {
				method: "POST",
				body: {
					process_id: selectedPid,
					query: q,
					top_k: 5
				}
			});
			if (selectedPidRef.current === requestProcessId && requestSequenceRef.current === requestId) setResult({
				process_id: requestProcessId,
				value: res
			});
		} catch (err) {
			if (selectedPidRef.current === requestProcessId && requestSequenceRef.current === requestId) {
				console.error("[Themis] Erro na pesquisa processual:", err);
				setError(err.message || String(err));
			}
		} finally {
			if (selectedPidRef.current === requestProcessId && requestSequenceRef.current === requestId) setLoading(false);
		}
	};
	const handleCitationClick = (citeNum) => {
		if (!result) return;
		const citation = (result.citations || []).find((c) => c.index === citeNum);
		if (citation) {
			if (onNavigateAutos) {
				const citationProcessId = citation.process_id || selectedPid;
				if (citationProcessId !== selectedPid) return;
				onNavigateAutos({
					process_id: citationProcessId,
					document_id: citation.document_id,
					pdf_page: citation.pdf_page,
					process_folio: citation.process_folio,
					source_line_ids: citation.source_line_ids,
					target_text: citation.excerpt,
					timestamp: Date.now()
				});
			}
		} else if (result.sources && result.sources[citeNum - 1]) {
			const src = result.sources[citeNum - 1];
			const sref = src.source_ref || {};
			if ((sref.process_id || src.process_id || selectedPid) !== selectedPid) return;
			if (onNavigateAutos) onNavigateAutos({
				process_id: selectedPid,
				document_id: sref.document_id || src.document_id,
				pdf_page: sref.pdf_page || src.page_number,
				process_folio: sref.process_folio,
				source_line_ids: sref.source_line_ids || src.source_line_ids,
				target_text: src.excerpt,
				timestamp: Date.now()
			});
		}
	};
	const handleSourceNavigateAutos = (src) => {
		const sref = src.source_ref || {};
		if (onNavigateAutos) {
			if ((sref.process_id || src.process_id || selectedPid) !== selectedPid) return;
			onNavigateAutos({
				process_id: selectedPid,
				document_id: sref.document_id || src.document_id,
				pdf_page: sref.pdf_page || src.page_number,
				process_folio: sref.process_folio,
				source_line_ids: sref.source_line_ids || src.source_line_ids,
				target_text: src.excerpt,
				timestamp: Date.now()
			});
		}
	};
	const handleSourceNavigatePdf = (src) => {
		const sref = src.source_ref || {};
		const documentId = sref.document_id || src.document_id;
		const pdfPage = Number(sref.pdf_page || src.page_number || 1);
		if (onNavigatePdf) {
			if ((sref.process_id || src.process_id || selectedPid) !== selectedPid) return;
			onNavigatePdf({
				process_id: selectedPid,
				document_id: documentId,
				pdf_page: pdfPage,
				timestamp: Date.now()
			});
		}
	};
	return jsxs("main", {
		className: "flex min-h-0 flex-1 flex-col overflow-hidden p-4 sm:p-5 gap-3.5",
		children: [
			jsx(PanelHeader, {
				title: "Pesquisa Processual & RAG",
				subtitle: "Consultas fundamentadas nos Autos com extração de evidências e citações verificáveis",
				actions: jsx(SegmentedControl, {
					options: [{
						id: "rag",
						label: "Resposta com Citações"
					}, {
						id: "search",
						label: "Evidências Diretas"
					}],
					value: searchMode,
					onChange: (mode) => {
						setSearchMode(mode);
						if (query.trim()) executeSearch(query, mode);
					},
					className: "shrink-0"
				})
			}),
			jsxs("div", {
				className: "flex flex-col gap-2.5 rounded-lg border border-border/60 bg-card/60 p-3.5 shadow-2xs backdrop-blur-xs",
				children: [jsxs("div", {
					className: "flex flex-wrap items-center justify-between gap-2",
					children: [jsx("span", {
						className: "text-xs font-semibold uppercase tracking-wider text-muted-foreground",
						children: `Processo: ${selectedPid || "nenhum processo selecionado"}`
					}), jsx("div", {
						className: "flex flex-wrap items-center gap-1.5",
						children: [
							{
								label: "Teor da comunicação e prazo",
								query: "Qual o teor da comunicação e o prazo fixado?"
							},
							{
								label: "Pedido da inicial",
								query: "Qual o pedido principal da petição inicial?"
							},
							{
								label: "Partes e procuradores",
								query: "Quem são as partes do processo e seus advogados constituídos?"
							},
							{
								label: "Tutela de urgência",
								query: "Consta nos autos requerimento ou deferimento de tutela de urgência ou liminar?"
							}
						].map((sug, sIdx) => {
							return jsxs("button", {
								type: "button",
								onClick: () => {
									setQuery(sug.query);
									executeSearch(sug.query, searchMode);
								},
								className: "inline-flex items-center gap-1 rounded-full border border-border/50 bg-muted/40 px-2.5 py-0.5 text-[0.7rem] text-muted-foreground transition-colors hover:border-primary/40 hover:bg-primary/5 hover:text-primary cursor-pointer",
								title: sug.query,
								children: [jsx(Codicon, {
									name: "sparkle",
									size: "0.65rem",
									className: "text-primary/70"
								}), jsx("span", { children: sug.label })]
							}, sIdx);
						})
					})]
				}), jsxs("div", {
					className: "flex items-end gap-2",
					children: [jsx("div", {
						className: "relative min-w-0 flex-1",
						children: jsx("textarea", {
							ref: textareaRef,
							rows: 2,
							value: query,
							onChange: (e) => {
								const nextVal = e.target.value;
								setQuery(nextVal);
								triggerWarmupIfValid(nextVal);
							},
							onKeyDown: (e) => {
								if (e.key === "Enter" && !e.shiftKey) {
									e.preventDefault();
									executeSearch();
								}
							},
							placeholder: "Faça uma pergunta sobre o processo (ex: Qual o teor da comunicação e o prazo fixado?)...",
							className: "w-full resize-none rounded-md border border-border/60 bg-background px-3 py-2 text-xs leading-relaxed text-foreground placeholder:text-muted-foreground/60 outline-none transition-colors hover:border-primary/50 focus:border-primary focus:ring-1 focus:ring-ring"
						})
					}), jsxs("div", {
						className: "flex flex-col gap-1.5 shrink-0",
						children: [jsx(Button, {
							variant: "primary",
							disabled: loading || !query.trim() || !selectedPid,
							onClick: () => executeSearch(),
							className: "h-8 px-3.5 text-xs font-medium gap-1.5",
							children: [jsx(Codicon, {
								name: loading ? "loading" : "search",
								className: loading ? "animate-spin" : ""
							}), jsx("span", { children: loading ? "Pesquisando..." : "Perguntar" })]
						}), query.trim() ? jsx(Button, {
							variant: "ghost",
							onClick: () => {
								setQuery("");
								warmupRequestedRef.current = false;
								if (textareaRef.current) textareaRef.current.focus();
							},
							className: "h-6 px-2 text-[0.7rem] text-muted-foreground hover:text-foreground",
							children: "Limpar"
						}) : null]
					})]
				})]
			}),
			jsxs("div", {
				className: "flex min-h-0 flex-1 flex-col overflow-hidden",
				children: [loading ? jsxs("div", {
					className: "flex min-h-0 flex-1 flex-col items-center justify-center p-8 gap-3 text-center",
					children: [
						jsx(Codicon, {
							name: "loading",
							size: "2rem",
							className: "animate-spin text-primary"
						}),
						jsx("div", {
							className: "text-sm font-semibold text-foreground",
							children: "Consultando Autos e sintetizando resposta fundamentada..."
						}),
						jsx("div", {
							className: "text-xs text-muted-foreground max-w-md",
							children: "Realizando busca vetorial ONNX + FTS BM25, extraindo evidências de layout e validando citações processuais."
						})
					]
				}) : error ? jsxs("div", {
					className: "rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-xs text-destructive space-y-2",
					children: [
						jsxs("div", {
							className: "flex items-center gap-2 font-semibold text-sm",
							children: [jsx(Codicon, {
								name: "error",
								className: "text-destructive"
							}), jsx("span", { children: "Falha na execução da pesquisa" })]
						}),
						jsx("div", {
							className: "text-muted-foreground leading-relaxed",
							children: error
						}),
						jsx(Button, {
							variant: "outline",
							onClick: () => executeSearch(),
							className: "text-xs h-7 mt-2",
							children: "Tentar novamente"
						})
					]
				}) : result ? jsxs("div", {
					className: "flex min-h-0 flex-1 flex-col overflow-y-auto overscroll-contain pr-1 space-y-4",
					"data-themis-page-scroll": "true",
					children: [result.answer ? jsxs("div", {
						className: "rounded-lg border border-primary/20 bg-primary/5 p-4 space-y-3 shadow-2xs",
						children: [
							jsxs("div", {
								className: "flex flex-wrap items-center justify-between gap-2 border-b border-primary/10 pb-2.5",
								children: [jsxs("div", {
									className: "flex items-center gap-2",
									children: [jsx(PanelPill, {
										tone: result.all_citations_verified !== false ? "good" : "warn",
										children: result.all_citations_verified !== false ? "Citações 100% Verificadas" : "Citações Parciais"
									}), jsx("span", {
										className: "text-xs font-mono font-medium text-muted-foreground",
										children: result.process_id || selectedPid
									})]
								}), jsx(Badge, {
									variant: "outline",
									className: "text-[0.68rem] font-normal text-muted-foreground",
									children: `${result.sources?.length || 0} fonte(s) recuperada(s)`
								})]
							}),
							jsx("div", {
								className: "text-xs leading-relaxed text-foreground/95",
								children: jsx(MarkdownDocument, {
									content: result.answer,
									onCitationClick: handleCitationClick
								})
							}),
							jsx("div", {
								className: "text-[0.7rem] text-muted-foreground/80 italic pt-1 border-t border-primary/10",
								children: "Dica: clique em qualquer indicador [1], [2] acima para navegar diretamente à página e fólio correspondente nos Autos."
							})
						]
					}) : null, result.sources && result.sources.length > 0 ? jsxs("div", {
						className: "space-y-2.5",
						children: [jsx(PanelSectionLabel, { children: `Fontes e Trechos Citados (${result.sources.length})` }), jsx("div", {
							className: "grid grid-cols-1 gap-2.5",
							children: result.sources.map((src, idx) => {
								const citeNum = idx + 1;
								const sref = src.source_ref || {};
								const folio = sref.process_folio;
								const pdfPage = sref.pdf_page || src.page_number || "?";
								const folioStr = folio !== null && folio !== void 0 ? `Fls. ${folio}` : `Pág. PDF ${pdfPage}`;
								const docId = sref.document_id || src.document_id || "";
								const docStr = docId ? `Doc ${docId.slice(0, 8)}...` : "";
								return jsxs("div", {
									className: "group rounded-lg border border-border/50 bg-card/50 p-3 text-xs space-y-2 transition-all hover:border-primary/40 hover:bg-card hover:shadow-2xs",
									children: [jsxs("div", {
										className: "flex items-center justify-between gap-2",
										children: [jsxs("div", {
											className: "flex items-center gap-2",
											children: [
												jsx("button", {
													type: "button",
													onClick: () => handleCitationClick(citeNum),
													className: "inline-flex items-center justify-center font-mono text-[0.72rem] font-bold text-primary bg-primary/10 hover:bg-primary/20 rounded px-1.5 py-0.5 cursor-pointer border border-primary/30 transition-colors",
													title: `Navegar para citação [${citeNum}] nos Autos`,
													children: `[${citeNum}]`
												}),
												jsx("span", {
													className: "font-semibold text-foreground",
													children: folioStr
												}),
												jsx("span", {
													className: "text-muted-foreground text-[0.68rem] font-mono",
													children: `(Pág. ${pdfPage}${docStr ? " · " + docStr : ""})`
												})
											]
										}), jsxs("div", {
											className: "flex items-center gap-1.5",
											children: [jsx(Button, {
												variant: "secondary",
												onClick: () => handleSourceNavigateAutos(src),
												className: "h-6 px-2 text-[0.7rem] gap-1 font-medium",
												title: "Abrir nos Autos do processo",
												children: [jsx(Codicon, {
													name: "book",
													size: "0.7rem"
												}), jsx("span", { children: "Abrir nos Autos" })]
											}), docId ? jsx(Button, {
												variant: "ghost",
												onClick: () => handleSourceNavigatePdf(src),
												className: "h-6 px-2 text-[0.7rem] gap-1 text-muted-foreground hover:text-foreground",
												title: "Visualizar página no PDF original",
												children: [jsx(Codicon, {
													name: "file-pdf",
													size: "0.7rem"
												}), jsx("span", { children: "PDF" })]
											}) : null]
										})]
									}), jsx("div", {
										className: "rounded border-l-2 border-primary/40 bg-muted/20 px-3 py-2 font-mono text-[0.72rem] leading-relaxed text-foreground/85 whitespace-pre-wrap max-h-36 overflow-y-auto",
										children: src.excerpt || "Trecho não disponível."
									})]
								}, `source-${idx}-${docId}-${pdfPage}`);
							})
						})]
					}) : null]
				}) : jsx(PanelEmpty, {
					icon: "search",
					title: "Pesquise nos Autos Processuais",
					description: "Faça uma pergunta sobre o processo selecionado acima para consultar atos, decisões, prazos e trechos com citações verificáveis."
				})]
			})
		]
	});
}
function handleThemisPageNavigation(event, rootOverride = null) {
	if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
	if (event.key !== "PageDown" && event.key !== "PageUp") return;
	const target = event.target;
	if (target?.closest?.("input, textarea, select, [contenteditable='true']")) return;
	const root = rootOverride || event.currentTarget;
	if (!root?.querySelectorAll || root.getClientRects?.().length === 0) return;
	let scroller = target?.closest?.("[data-themis-page-scroll='true']");
	if (!scroller || scroller.scrollHeight <= scroller.clientHeight) {
		let candidates = Array.from(root.querySelectorAll("[data-themis-page-scroll='true']")).filter((node) => node.getClientRects().length > 0 && node.scrollHeight > node.clientHeight);
		if (candidates.length === 0) candidates = Array.from(root.querySelectorAll("*")).filter((node) => {
			if (node.getClientRects().length === 0 || node.scrollHeight <= node.clientHeight) return false;
			const overflowY = getComputedStyle(node).overflowY;
			return overflowY === "auto" || overflowY === "scroll";
		});
		scroller = candidates.sort((a, b) => b.clientHeight - a.clientHeight)[0] || null;
	}
	if (!scroller) return;
	event.preventDefault();
	const direction = event.key === "PageDown" ? 1 : -1;
	scroller.scrollBy({ top: direction * Math.max(80, Math.floor(scroller.clientHeight * 0.88)), behavior: "auto" });
}
function ThemisShell({ ctx }) {
	const themisRootRef = useRef(null);
	const [activeTab, setActiveTab] = useState(() => {
		const saved = ctx.storage.get("workspace.activeModule", "eventos");
		return saved === "pesquisa" ? "processos" : saved;
	});
	const [navTarget, setNavTarget] = useState(null);
	const [events, setEvents] = useState([]);
	const [processes, setProcesses] = useState([]);
	const [djenStatus, setDjenStatus] = useState(null);
	const [djenSyncing, setDjenSyncing] = useState(false);
	const [djenError, setDjenError] = useState(null);
	const djenPollRef = useRef(false);
	const [loading, setLoading] = useState(true);
	const [fetchError, setFetchError] = useState(null);
	useEffect(() => {
		const onPageNavigation = (event) => handleThemisPageNavigation(event, themisRootRef.current);
		window.addEventListener("keydown", onPageNavigation, { capture: true });
		return () => window.removeEventListener("keydown", onPageNavigation, { capture: true });
	}, []);
	const [selectedId, setSelectedId] = useState("");
	const [filterProcess, setFilterProcess] = useState("todos");
	const [filterType, setFilterType] = useState("todos");
	const [search, setSearch] = useState("");
	const [listWidthPct, setListWidthPct] = useState(45);
	const [isDragging, setIsDragging] = useState(false);
	const splitContainerRef = useRef(null);
	const handleNavigateAutos = (target) => {
		setNavTarget({
			...target,
			section: "autos",
			timestamp: Date.now()
		});
		setActiveTab("processos");
	};
	const handleNavigatePdf = (target) => {
		setNavTarget({
			...target,
			section: "pdf",
			timestamp: Date.now()
		});
		setActiveTab("processos");
	};
	useEffect(() => {
		ctx.storage.set("workspace.activeModule", activeTab);
	}, [ctx, activeTab]);
	const loadEvents = useCallback(async () => {
		const data = await ctx.rest("/events");
		const adapted = (Array.isArray(data) ? data : []).map(adaptLegalEventToUI);
		setEvents(adapted);
		setFetchError(null);
		setLoading(false);
		return adapted;
	}, [ctx]);
	const watchDjenJob = useCallback(async (job) => {
		if (!job?.job_id || djenPollRef.current) return;
		djenPollRef.current = true;
		setDjenSyncing(true);
		setDjenError(null);
		try {
			let current = job;
			while (["PENDING", "RUNNING"].includes(String(current?.status || "").toUpperCase())) {
				setDjenStatus((previous) => ({ ...previous, active_job: current, latest_job: current }));
				await new Promise((resolve) => setTimeout(resolve, 1200));
				current = await ctx.rest(`/djen/jobs/${encodeURIComponent(job.job_id)}`);
				const status = await ctx.rest("/djen/status");
				setDjenStatus(status);
			}
			if (String(current?.status || "").toUpperCase() === "FAILED") throw new Error(current.error || "Falha ao atualizar DJEN.");
			if (String(current?.status || "").toUpperCase() !== "COMPLETED") throw new Error("O job DJEN terminou em estado inválido.");
			setDjenStatus(await ctx.rest("/djen/status"));
			await loadEvents();
			return current;
		} catch (error) {
			console.error("[Themis] Falha ao sincronizar DJEN:", error);
			setDjenError(error.message || String(error));
			throw error;
		} finally {
			djenPollRef.current = false;
			setDjenSyncing(false);
		}
	}, [ctx, loadEvents]);
	const refreshDjen = useCallback(async (automatic = false) => {
		if (djenPollRef.current) return;
		try {
			const body = filterProcess === "todos" ? {} : { process_id: filterProcess };
			const response = await ctx.rest("/djen/sync-now", { method: "POST", body });
			return await watchDjenJob(response?.job || response);
		} catch (error) {
			if (!automatic) throw error;
			return null;
		}
	}, [ctx, filterProcess, watchDjenJob]);
	useEffect(() => {
		let cancelled = false;
		setLoading(true);
		Promise.all([ctx.rest("/tree"), ctx.rest("/djen/status"), loadEvents()]).then(async ([tree, status]) => {
			if (cancelled) return;
			setProcesses(Array.isArray(tree?.processes) ? tree.processes : []);
			setDjenStatus(status);
			if (status?.active_job) await watchDjenJob(status.active_job).catch(() => null);
			else if (status?.needs_sync) await refreshDjen(true);
		}).catch((err) => {
			if (cancelled) return;
			console.error("[Themis Plugin] Erro ao carregar Eventos/DJEN:", err);
			setFetchError(err.message || String(err));
			setLoading(false);
		});
		return () => {
			cancelled = true;
		};
	}, [ctx, loadEvents]);
	const filterOptions = useMemo(() => [
		{
			id: "todos",
			label: `Todos (${events.length})`
		},
		{
			id: "publicacao",
			label: "Publicações"
		},
		{
			id: "prazo",
			label: "Prazos"
		},
		{
			id: "audiencia",
			label: "Audiências"
		},
		{
			id: "pendencia",
			label: "Pendências"
		}
	], [events.length]);
	const filteredEventos = useMemo(() => {
		return events.filter((evt) => {
			const matchProcess = filterProcess === "todos" || evt.processo === filterProcess;
			const matchFilter = filterType === "todos" || evt.tipo === filterType;
			const matchSearch = !search || evt.titulo.toLowerCase().includes(search.toLowerCase()) || evt.processo.toLowerCase().includes(search.toLowerCase()) || evt.teor.toLowerCase().includes(search.toLowerCase());
			return matchProcess && matchFilter && matchSearch;
		});
	}, [
		events,
		filterProcess,
		filterType,
		search
	]);
	const sortedEventos = useMemo(() => {
		return [...filteredEventos].sort((a, b) => {
			const aDate = a.data || "0000-00-00";
			const bDate = b.data || "0000-00-00";
			const dateCompare = bDate.localeCompare(aDate);
			if (dateCompare !== 0) return dateCompare;
			const aDeadline = a.tipo === "prazo";
			const bDeadline = b.tipo === "prazo";
			if (aDeadline !== bDeadline) return aDeadline ? -1 : 1;
			const timeCompare = (b.horario || "").localeCompare(a.horario || "");
			if (timeCompare !== 0) return timeCompare;
			return String(b.id || "").localeCompare(String(a.id || ""));
		});
	}, [filteredEventos]);
	const selectedEvent = useMemo(() => {
		if (selectedId) {
			const found = sortedEventos.find((evt) => evt.id === selectedId);
			if (found) return found;
		}
		return sortedEventos[0] || null;
	}, [selectedId, sortedEventos]);
	const handleNavigatePublication = (eventId) => {
		if (!eventId) return;
		setFilterType("todos");
		setSelectedId(eventId);
		requestAnimationFrame(() => {
			requestAnimationFrame(() => {
				const rows = Array.from(document.querySelectorAll("[data-themis-event-id]"));
				const target = rows.find((node) => node.dataset.themisEventId === eventId);
				target?.scrollIntoView?.({ block: "center", behavior: "smooth" });
			});
		});
	};
	const selectedMetaRows = useMemo(() => (selectedEvent?.meta || []).map((row, index) => {
		if (row.action === "autos" && row.target) return {
			...row,
			value: jsx("button", {
				type: "button",
				className: "inline-flex items-center gap-1 text-left text-primary hover:underline underline-offset-2 cursor-pointer",
				onClick: () => handleNavigateAutos(row.target),
				children: [row.value, jsx(Codicon, { name: "go-to-file", size: "0.72rem", className: "shrink-0 opacity-70" }, "icon")]
			})
		};
		if (row.action === "publication" && row.target) return {
			...row,
			value: jsx("button", {
				type: "button",
				className: "inline-flex items-center gap-1 text-left text-primary hover:underline underline-offset-2 cursor-pointer",
				onClick: () => handleNavigatePublication(row.target),
				children: [row.value, jsx(Codicon, { name: "arrow-right", size: "0.72rem", className: "shrink-0 opacity-70" }, "icon")]
			})
		};
		return row;
	}), [selectedEvent]);
	const handlePointerDown = (e) => {
		e.preventDefault();
		setIsDragging(true);
		const container = splitContainerRef.current;
		if (!container) return;
		const containerRect = container.getBoundingClientRect();
		const handlePointerMove = (moveEvent) => {
			const offsetX = moveEvent.clientX - containerRect.left;
			const totalWidth = containerRect.width;
			if (totalWidth <= 0) return;
			let newPct = offsetX / totalWidth * 100;
			const minPct = Math.max(18, 220 / totalWidth * 100);
			const maxPct = Math.min(72, (totalWidth - 280) / totalWidth * 100);
			newPct = Math.max(minPct, Math.min(maxPct, newPct));
			setListWidthPct(newPct);
		};
		const handlePointerUp = () => {
			setIsDragging(false);
			window.removeEventListener("pointermove", handlePointerMove);
			window.removeEventListener("pointerup", handlePointerUp);
		};
		window.addEventListener("pointermove", handlePointerMove);
		window.addEventListener("pointerup", handlePointerUp);
	};
	const handleDoubleClick = () => {
		setListWidthPct(45);
	};
	const selectedDjenState = useMemo(() => {
		const states = Array.isArray(djenStatus?.processes) ? djenStatus.processes : [];
		if (filterProcess !== "todos") return states.find((item) => item.process_id === filterProcess) || null;
		const synced = states.filter((item) => item.last_successful_sync_at);
		if (synced.length === 0) return null;
		return synced.sort((a, b) => String(a.last_successful_sync_at).localeCompare(String(b.last_successful_sync_at)))[0];
	}, [djenStatus, filterProcess]);
	const djenSyncedAt = selectedDjenState?.last_successful_sync_at ? new Date(selectedDjenState.last_successful_sync_at) : null;
	const djenStatusLabel = djenSyncing ? "Atualizando DJEN…" : djenSyncedAt && !Number.isNaN(djenSyncedAt.getTime()) ? `DJEN atualizado ${djenSyncedAt.toLocaleDateString("pt-BR")} às ${djenSyncedAt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}` : "DJEN ainda não atualizado";
	const filterActions = jsxs("div", {
		className: "flex min-w-0 items-center gap-3",
		children: [
			jsxs(Select, {
				value: filterProcess,
				onValueChange: setFilterProcess,
				children: [jsx(SelectTrigger, {
					className: "h-7 w-56 max-w-56 rounded-md text-[0.7rem]",
					"aria-label": "Filtrar por processo",
					children: jsx(SelectValue, { placeholder: "Todos os processos" })
				}), jsxs(SelectContent, {
					children: [jsx(SelectItem, { value: "todos", children: "Todos os processos" }), ...processes.map((process) => {
						const pid = process.process_id || process.id || "";
						return jsx(SelectItem, { value: pid, children: pid }, pid);
					})]
				})]
			}),
			jsxs("div", {
				className: "flex items-center gap-2 rounded-md bg-muted/35 px-2 py-1",
				children: [jsx(Codicon, {
					name: "sync",
					size: "0.75rem",
					className: "text-muted-foreground/80"
				}), jsx("span", {
					className: "hidden 2xl:inline text-[0.68rem] text-muted-foreground whitespace-nowrap",
					children: djenStatusLabel
				}), jsx(Button, {
					variant: "secondary",
					size: "sm",
					disabled: djenSyncing,
					onClick: () => refreshDjen(false).catch(() => {}),
					className: "h-6 px-2 text-[0.68rem]",
					title: "Sincronizar publicações do DJEN",
					children: djenSyncing ? "Atualizando DJEN…" : "Atualizar DJEN"
				})]
			}),
			jsx(SegmentedControl, {
				options: filterOptions,
				value: filterType,
				onChange: setFilterType,
				className: "shrink-0"
			})
		]
	});
	return jsxs("div", {
		ref: themisRootRef,
		className: "flex h-full w-full flex-col overflow-hidden bg-background text-foreground select-text",
		children: [jsxs("header", {
			className: "flex h-7 shrink-0 select-none items-stretch justify-between border-b border-border/40 bg-(--ui-sidebar-surface-background,var(--muted)) px-2",
			children: [jsxs("div", {
				className: "flex items-center gap-1.5 pr-3 text-[0.6875rem] font-semibold tracking-wider text-foreground uppercase",
				children: [jsx(Codicon, {
					name: "law",
					className: "text-primary"
				}), jsx("span", { children: "Themis" })]
			}), jsx("nav", {
				className: "flex h-full items-stretch min-w-0",
				role: "tablist",
				children: NAV_TABS.map((tab) => {
					const active = activeTab === tab.id;
					return jsxs("button", {
						type: "button",
						role: "tab",
						"aria-selected": active,
						onClick: () => setActiveTab(tab.id),
						className: cn("group/tab relative flex h-full items-center gap-1.5 px-3 text-[9px] font-medium tracking-wide uppercase transition-colors outline-none cursor-pointer", "not-first:border-l not-first:border-l-border/20", active ? "text-foreground shadow-[inset_0_-2px_0_var(--pane-tab-active-accent,var(--theme-primary))] font-semibold bg-background/50" : "text-(--ui-text-tertiary,var(--muted-foreground)) hover:text-foreground hover:bg-muted/30"),
						children: [jsx(Codicon, {
							name: tab.icon,
							size: "0.8rem"
						}), jsx("span", { children: tab.label })]
					}, tab.id);
				})
			})]
		}), activeTab === "eventos" ? jsxs("main", {
			className: "flex min-h-0 flex-1 flex-col overflow-hidden p-4 sm:p-5 gap-3",
			children: [jsx(PanelHeader, {
				title: "Eventos Processuais",
				subtitle: "Cronologia unificada de publicações, prazos, audiências e pendências",
				actions: filterActions
			}), djenError ? jsx("div", {
				className: "rounded-md bg-destructive/8 px-3 py-2 text-[0.72rem] text-destructive",
				children: `Falha ao atualizar DJEN: ${djenError}`
			}) : null, jsxs("div", {
				ref: splitContainerRef,
				className: cn("flex min-h-0 flex-1 flex-row overflow-hidden", isDragging && "select-none"),
				children: [
					jsx("div", {
						style: {
							flex: `0 0 ${listWidthPct}%`,
							width: `${listWidthPct}%`,
							minWidth: "220px",
							maxWidth: "calc(100% - 280px)"
						},
						className: "flex min-h-0 min-w-0 flex-col overflow-hidden pr-1",
						children: jsx(PanelList, {
							className: "w-full min-[47.5rem]:w-full min-w-0 flex-1 h-full min-h-0 max-w-none [&_input]:w-full [&_input]:min-w-0 [&_input]:flex-1",
							searchValue: search,
							onSearchChange: setSearch,
							searchPlaceholder: "Filtrar eventos...",
							children: loading ? jsx("div", {
								className: "p-4 text-center text-xs text-muted-foreground",
								children: "Carregando eventos do Core..."
							}) : fetchError ? jsxs("div", {
								className: "p-4 text-center text-xs text-destructive space-y-1",
								children: [jsx("div", {
									className: "font-semibold",
									children: "Falha na conexão com o Core"
								}), jsx("div", {
									className: "text-[0.6875rem] text-muted-foreground",
									children: fetchError
								})]
							}) : sortedEventos.length === 0 ? jsx("div", {
								className: "p-4 text-center text-xs text-muted-foreground",
								children: "Nenhum evento correspondente"
							}) : jsx("div", {
								role: "list",
								"aria-label": "Eventos processuais",
								className: "flex flex-col gap-0.5 p-1",
								children: sortedEventos.map((evt) => {
									const active = selectedEvent?.id === evt.id;
									const dateLabel = evt.dataExibicao + (evt.horario ? " · " + evt.horario : "");
									return jsxs("button", {
										type: "button",
										role: "listitem",
										"aria-current": active ? "true" : void 0,
										"data-themis-event-id": evt.id,
										onClick: () => setSelectedId(evt.id),
										className: cn("group/row flex w-full items-center gap-2 rounded-md px-2 py-1 text-left transition-colors cursor-pointer", active ? "bg-(--ui-row-active-background,var(--muted)) text-foreground font-medium" : "text-(--ui-text-secondary,var(--muted-foreground)) hover:bg-muted/40 hover:text-foreground"),
										children: [
											jsx(Codicon, {
												name: evt.codicon || "circle-outline",
												size: "0.8rem",
												className: cn("shrink-0", evt.urgencyClass || (active ? "text-foreground/85" : "text-muted-foreground/75"))
											}),
											jsx("span", {
												className: cn("w-24 shrink-0 font-mono text-[0.68rem] tabular-nums", evt.urgencyClass || "text-muted-foreground/80"),
												children: dateLabel
											}),
											jsx("span", {
												className: cn("min-w-0 flex-1 truncate text-[0.75rem]", evt.urgencyClass),
												title: evt.titulo,
												children: evt.titulo
											}),
											filterProcess === "todos" && evt.processo ? jsx("span", {
												className: "hidden min-[72rem]:inline max-w-40 shrink-0 truncate font-mono text-[0.63rem] text-muted-foreground/55",
												title: evt.processo,
												children: evt.processo
											}) : null
										]
									}, evt.id);
								})
							})
						})
					}),
					jsxs("div", {
						role: "separator",
						"aria-orientation": "vertical",
						"aria-valuenow": Math.round(listWidthPct),
						onPointerDown: handlePointerDown,
						onDoubleClick: handleDoubleClick,
						className: cn("group relative flex w-2.5 shrink-0 cursor-col-resize select-none items-center justify-center transition-colors", isDragging && "cursor-col-resize"),
						style: { touchAction: "none" },
						title: "Arraste para redimensionar (duplo clique para restaurar)",
						children: [jsx("div", { className: cn("h-full w-px bg-border/40 transition-all duration-150", "group-hover:w-0.5 group-hover:bg-primary/50", isDragging && "w-0.5 bg-primary") })]
					}),
					jsx("div", {
						style: {
							flex: "1 1 0%",
							minWidth: "280px"
						},
						className: "flex min-h-0 min-w-0 flex-col overflow-hidden pl-2",
						children: selectedEvent ? jsxs(PanelDetail, {
							className: "flex min-h-0 flex-1 flex-col overflow-hidden pr-1",
							children: [
								jsxs("div", {
									className: "flex items-start justify-between gap-3 border-b border-border/40 pb-3",
									children: [jsxs("div", {
										className: "min-w-0 flex-1 space-y-1",
										children: [jsxs("div", {
											className: "flex items-center gap-2",
											children: [jsx(PanelPill, {
												tone: selectedEvent.tone,
												children: selectedEvent.tipoLabel
											}), selectedEvent.processo ? jsx("span", {
												className: "text-xs font-mono text-muted-foreground",
												children: selectedEvent.processo
											}) : null]
										}), jsx("h2", {
											className: "text-base font-semibold text-foreground",
											children: selectedEvent.titulo
										})]
									}), jsx(Badge, {
										variant: "outline",
										className: "text-[0.68rem] font-normal text-muted-foreground/80",
										children: `${selectedEvent.dataExibicao}${selectedEvent.horario ? " · " + selectedEvent.horario : ""}`
									})]
								}),
								selectedEvent.meta && selectedEvent.meta.length > 0 ? jsxs("div", {
									className: "shrink-0",
									children: [jsx(PanelSectionLabel, { children: selectedEvent.tipo === "prazo" ? "Trilha do prazo" : "Metadados & Identificação" }), jsx(PanelMeta, { rows: selectedMetaRows })]
								}) : null,
								jsxs("div", {
									className: "flex min-h-0 flex-1 flex-col pt-1",
									children: [jsx(PanelSectionLabel, { children: selectedEvent.tipo === "prazo" ? "Determinação judicial" : "Teor / Conteúdo do Ato" }), jsx("div", {
										className: "themis-scroll-visible min-h-0 flex-1 overflow-y-auto rounded-md bg-muted/20 p-3",
										"data-themis-page-scroll": "true",
										children: jsxs("div", {
											className: "space-y-4",
											children: [jsx("div", {
												className: "whitespace-pre-wrap text-[0.78rem] leading-relaxed text-foreground/90",
												children: selectedEvent.teor
											}), selectedEvent.providencias ? jsxs("div", {
												className: "space-y-2",
												children: [jsx(PanelSectionLabel, { children: "Providências & Ações" }), jsx("div", {
													className: "rounded-md bg-primary/5 p-3 text-xs leading-relaxed text-foreground/90",
													children: selectedEvent.providencias
												})]
											}) : null]
										})
									})]
								})
							]
						}) : jsx(PanelEmpty, {
							icon: "inbox",
							title: "Nenhum evento selecionado",
							description: "Selecione um evento na lista à esquerda para visualizar seus detalhes completos."
						})
					})
				]
			})]
		}) : activeTab === "processos" ? jsx(ProcessosView, {
			ctx,
			navTarget,
			onNavigateAutos: handleNavigateAutos,
			onNavigatePdf: handleNavigatePdf
		}) : jsxs("main", {
			className: "flex min-h-0 flex-1 flex-col items-center justify-center p-8",
			children: [jsx(PanelEmpty, {
				icon: NAV_TABS.find((t) => t.id === activeTab)?.icon || "inbox",
				title: `Módulo ${NAV_TABS.find((t) => t.id === activeTab)?.label}`,
				description: "Este módulo está previsto no roadmap canônico do Themis e será implementado nos próximos slices."
			})]
		})]
	});
}
var themisDesktopPluginsRoot = await window.hermesDesktop.desktopPluginsRoot();
var themisPathSep = themisDesktopPluginsRoot.includes("\\") ? "\\" : "/";
var themisHermesRoot = themisDesktopPluginsRoot.replace(/[\\/]desktop-plugins[\\/]?$/, "");
var themisFontsCss = [
	themisHermesRoot,
	"plugins",
	"themis",
	"assets",
	"fonts",
	"fonts.css"
].join(themisPathSep);
var themisTheme = {
	name: "themis",
	label: "Themis",
	description: "Themis — quiet dark workspace",
	colors: {
		background: "#f5f5f3",
		foreground: "#20201e",
		card: "#eeeeeb",
		cardForeground: "#20201e",
		muted: "#e8e8e4",
		mutedForeground: "#73736e",
		popover: "#f0f0ed",
		popoverForeground: "#20201e",
		primary: "#555955",
		primaryForeground: "#ffffff",
		secondary: "#e5e5e1",
		secondaryForeground: "#30302d",
		accent: "#deded9",
		accentForeground: "#30302d",
		border: "transparent",
		input: "#e1e1dd",
		ring: "#777b76",
		midground: "#696d68",
		destructive: "#b94a3a",
		destructiveForeground: "#ffffff",
		sidebarBackground: "#eeeeeb",
		sidebarBorder: "transparent",
		userBubble: "#e9e9e5",
		userBubbleBorder: "transparent"
	},
	darkColors: {
		background: "#171717",
		foreground: "#e7e7e5",
		card: "#1d1d1d",
		cardForeground: "#e7e7e5",
		muted: "#222222",
		mutedForeground: "#9c9c97",
		popover: "#222222",
		popoverForeground: "#e7e7e5",
		primary: "#9da19b",
		primaryForeground: "#171717",
		secondary: "#242424",
		secondaryForeground: "#d8d8d5",
		accent: "#292929",
		accentForeground: "#e7e7e5",
		border: "transparent",
		input: "#272727",
		ring: "#777b76",
		midground: "#858a83",
		destructive: "#c45c50",
		destructiveForeground: "#ffffff",
		sidebarBackground: "#191919",
		sidebarBorder: "transparent",
		userBubble: "#242424",
		userBubbleBorder: "transparent",
		banner_border: "transparent",
		response_border: "transparent",
		session_border: "transparent"
	},
	typography: {
		fontSans: "\"Inter\", -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, system-ui, sans-serif",
		fontMono: "\"RobotoMono\", \"SF Mono\", Menlo, Consolas, \"Liberation Mono\", monospace",
		fontUrl: themisFontsCss
	}
};
var plugin_default = {
	id: "themis",
	name: "Themis",
	register(ctx) {
		ctx.registerMany([
			{
				id: "page",
				area: ROUTES_AREA,
				data: { path: "/themis" },
				render: () => jsx(ThemisShell, { ctx })
			},
			{
				id: "nav",
				area: SIDEBAR_NAV_AREA,
				data: {
					path: "/themis",
					label: "Themis",
					codicon: "law"
				}
			},
			{
				id: "theme",
				area: THEMES_AREA,
				data: themisTheme
			}
		]);
	}
};
//#endregion
export { plugin_default as default };
