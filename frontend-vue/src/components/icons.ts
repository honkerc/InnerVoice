import { defineComponent, h } from "vue";

const strokeIcon = {
  fill: "none",
  stroke: "currentColor",
  "stroke-width": "1.8",
  "stroke-linecap": "round",
  "stroke-linejoin": "round",
};

function icon(
  name: string,
  paths: ReturnType<typeof h>[],
  defaults: { size?: number } = {},
) {
  return defineComponent({
    name,
    props: {
      size: { type: Number, default: defaults.size ?? 16 },
      class: { type: String, default: "" },
      filled: { type: Boolean, default: false },
    },
    setup(props) {
      return () =>
        h(
          "svg",
          {
            width: props.size,
            height: props.size,
            viewBox: "0 0 24 24",
            class: props.class,
            "aria-hidden": "true",
            ...(name === "IconPin"
              ? {
                  fill: props.filled ? "currentColor" : "none",
                  stroke: "currentColor",
                  "stroke-width": "2",
                }
              : strokeIcon),
          },
          paths,
        );
    },
  });
}

export const IconChevronLeft = icon("IconChevronLeft", [h("path", { d: "M15 6l-6 6 6 6" })], { size: 18 });
export const IconChevronDown = icon("IconChevronDown", [h("path", { d: "M6 9l6 6 6-6" })], { size: 18 });
export const IconCopy = icon("IconCopy", [
  h("rect", { x: "9", y: "9", width: "13", height: "13", rx: "2" }),
  h("path", { d: "M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" }),
]);
export const IconCheck = icon("IconCheck", [h("path", { d: "M5 13l4 4L19 7", "stroke-width": "2" })]);
export const IconQuote = icon("IconQuote", [
  h("path", { d: "M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" }),
  h("path", { d: "M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" }),
]);
export const IconSun = icon("IconSun", [
  h("circle", { cx: "12", cy: "12", r: "4" }),
  h("path", { d: "M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" }),
], { size: 18 });
export const IconMoon = icon("IconMoon", [
  h("path", { d: "M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" }),
], { size: 18 });
export const IconTemplate = icon("IconTemplate", [
  h("rect", { x: "4", y: "3", width: "16", height: "18", rx: "2" }),
  h("path", { d: "M8 8h8M8 12h8M8 16h5" }),
], { size: 18 });
export const IconSearch = icon("IconSearch", [
  h("circle", { cx: "11", cy: "11", r: "7" }),
  h("path", { d: "M21 21l-4.3-4.3" }),
]);
export const IconChart = icon("IconChart", [
  h("path", { d: "M4 19V5" }),
  h("path", { d: "M4 19h16" }),
  h("path", { d: "M8 17V9" }),
  h("path", { d: "M12 17V7" }),
  h("path", { d: "M16 17v-4" }),
]);
export const IconPin = icon("IconPin", [h("path", { d: "M16 12V4h1V2H7v2h1v8l-2 2v2h5v6l1 1 1-1v-6h5v-2l-2-2z" })], {
  size: 13,
});
export const IconClose = icon("IconClose", [h("path", { d: "M18 6L6 18M6 6l12 12", "stroke-width": "2" })], {
  size: 14,
});
export const IconEdit = icon("IconEdit", [
  h("path", { d: "M12 20h9" }),
  h("path", { d: "M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4z" }),
]);
export const IconFile = icon("IconFile", [
  h("path", { d: "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" }),
  h("path", { d: "M14 2v6h6" }),
]);
export const IconVideo = icon("IconVideo", [
  h("rect", { x: "2", y: "6", width: "14", height: "12", rx: "2" }),
  h("path", { d: "M16 10l6-3v10l-6-3" }),
]);
export const IconAttach = icon("IconAttach", [
  h("path", {
    d: "M21.44 11.05l-9.19 9.19a5.5 5.5 0 01-7.78-7.78l9.19-9.19a3.5 3.5 0 014.95 4.95l-9.2 9.19a1.5 1.5 0 01-2.12-2.12l8.49-8.48",
  }),
]);
export const IconTrash = icon("IconTrash", [
  h("path", { d: "M3 6h18" }),
  h("path", { d: "M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2" }),
  h("path", { d: "M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" }),
  h("path", { d: "M10 11v6M14 11v6" }),
]);
export const IconRefresh = icon("IconRefresh", [
  h("path", { d: "M21 12a9 9 0 11-3-6.7" }),
  h("path", { d: "M21 3v6h-6" }),
]);
export const IconCalendar = icon("IconCalendar", [
  h("rect", { x: "3", y: "4", width: "18", height: "18", rx: "2" }),
  h("path", { d: "M16 2v4M8 2v4M3 10h18" }),
]);
export const GearIcon = icon(
  "GearIcon",
  [
    h("path", {
      d: "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z",
    }),
    h("circle", { cx: "12", cy: "12", r: "3" }),
  ],
  { size: 18 },
);
