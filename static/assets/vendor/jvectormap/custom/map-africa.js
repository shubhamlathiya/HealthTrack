// Africa
$(function () {
    $("#mapAfrica").vectorMap({
        map: "africa_mill",
        backgroundColor: "transparent",
        scalecolors: ["#566fe2"],
        zoomOnScroll: false,
        zoomMin: 1,
        hoverColor: true,
        series: {
            regions: [
                {
                    values: gdpData,
                    scale: ["#566fe2"],
                    normalizeFunction: "polynomial",
                },
            ],
        },
    });
});
