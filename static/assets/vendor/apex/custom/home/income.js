var options = {
  chart: {
    height: 345,
    type: "area",
    toolbar: {
      show: false,
    },
  },
  dataLabels: {
    enabled: false,
  },

  plotOptions: {
    bar: {
      columnWidth: "20%",
      borderRadius: 6,
    },
  },
  stroke: {
    show: true,
    width: 2,
    colors: ["#566FE2", "#6480E7", "#7292EC", "#80A3F1", "#8EB4F5", "#9CC6FA", "#AAD7FF"],
  },
  series: [
    {
      name: "Appointments",
      type: "column",
      data: [10, 40, 15, 40, 20, 35, 20, 10, 31, 43, 56, 29],
    },
    {
      name: "Surgeries",
      type: "area",
      data: [2, 8, 25, 7, 20, 20, 51, 35, 42, 20, 33, 67],
    },
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
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
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
    strokeWidth: 2,
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
    theme: 'dark',
  },
};

var chart = new ApexCharts(document.querySelector("#income"), options);
chart.render();