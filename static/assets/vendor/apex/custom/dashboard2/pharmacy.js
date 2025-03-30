var options = {
  chart: {
    height: 260,
    type: "area",
    toolbar: {
      show: false,
    },
  },
  dataLabels: {
    enabled: false,
  },
  stroke: {
    curve: "smooth",
    width: 4,
  },
  series: [
    {
      name: "Pharmacy Sales",
      data: [0, 1000, 4000, 3000, 6000, 2000, 3000],
    }
  ],
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
      top: 0,
      right: 0,
      bottom: 0,
      left: 0,
    },
  },
  xaxis: {
    categories: [
      "Sun",
      "Mon",
      "Tue",
      "Wed",
      "Thu",
      "Fri",
      "Sat",
    ],
  },
  yaxis: {
    labels: {
      show: false,
    },
  },
  colors: ["#566FE2", "#6480E7", "#7292EC", "#80A3F1", "#8EB4F5", "#9CC6FA", "#AAD7FF"],
  markers: {
    size: 0,
    opacity: 0.3,
    colors: ["#566FE2", "#6480E7", "#7292EC", "#80A3F1", "#8EB4F5", "#9CC6FA", "#AAD7FF"],
    strokeColor: "#ffffff",
    strokeWidth: 1,
    hover: {
      size: 7,
    },
  },
  tooltip: {
    y: {
      formatter: function (val) {
        return val;
      },
    },
  },
};

var chart = new ApexCharts(document.querySelector("#pharmacy"), options);

chart.render();