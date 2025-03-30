// Europe
$(function () {
  $("#mapEurope").vectorMap({
    map: "europe_mill",
    zoomOnScroll: false,
    series: {
      regions: [
        {
          values: gdpData,
          scale: ["#566fe2"],
          normalizeFunction: "polynomial",
        },
      ],
    },
    backgroundColor: "transparent",
  });
});
