var options = {
    chart: {
        width: 360,
        type: "pie",
    },
    labels: ["Cardiology", "Orthopedics", "Neurology", "Gastroenterology", "Anatomy"],
    series: [50, 40, 30, 20, 10],
    legend: {
        position: "bottom",
    },
    dataLabels: {
        enabled: false,
    },
    stroke: {
        width: 0,
    },
    colors: [
        "#566FE2", "#6480E7", "#7292EC", "#80A3F1", "#8EB4F5", "#9CC6FA", "#AAD7FF"
    ],
};
var chart = new ApexCharts(document.querySelector("#total-department"), options);
chart.render();