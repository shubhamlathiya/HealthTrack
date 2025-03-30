var options = {
  chart: {
    height: 185,
    type: "bar",
    toolbar: {
      show: false,
    },
  },
  plotOptions: {
    bar: {
      columnWidth: "70%",
      borderRadius: 2,
      distributed: true,
      dataLabels: {
        position: "center",
      },
    },
  },
  series: [
    {
      name: "Claims",
      data: [30, 60, 70, 80, 70, 60, 30],
    },
  ],
  legend: {
    show: false,
  },
  xaxis: {
    categories: [
      "S",
      "M",
      "T",
      "W",
      "T",
      "F",
      "S",
    ],
    axisBorder: {
      show: false,
    },
    yaxis: {
      show: false,
    },
    tooltip: {
      enabled: true,
    },
    labels: {
      show: true,
    },
  },
  grid: {
    borderColor: "#d8dee6",
    strokeDashArray: 5,
    xaxis: {
      lines: {
        show: true,
      },
    },
    yaxis: {
      lines: {
        show: false,
      },
    },
    padding: {
      left: 0,
      top: 0,
      right: 0,
      bottom: 0,
    },
  },
  yaxis: {
    labels: {
      show: false,
    },
  },
  tooltip: {
    y: {
      formatter: function (val) {
        return val;
      },
    },
  },
  colors: [
    "#566FE2", "#6480E7", "#7292EC", "#80A3F1", "#8EB4F5", "#9CC6FA", "#AAD7FF"
  ],
};
var chart = new ApexCharts(document.querySelector("#claims"), options);
chart.render();