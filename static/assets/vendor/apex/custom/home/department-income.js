var options = {
  chart: {
    height: 300,
    type: "line",
    toolbar: {
      show: false,
    },
  },
  dataLabels: {
    enabled: false,
  },
  fill: {
    type: 'solid',
    opacity: [.1, 1, .5, 1],
  },
  stroke: {
    curve: "smooth",
    width: [0, 0, 0, 4]
  },
  series: [{
    name: 'Neurology',
    type: 'bar',
    data: [400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950]
  }, {
    name: 'Dental Care',
    type: 'bar',
    data: [300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850]
  }, {
    name: 'Gynocology',
    type: 'bar',
    data: [200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750]
  }, {
    name: 'Orthopedic',
    type: 'line',
    data: [100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650]
  }],
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
    strokeWidth: 1,
    hover: {
      size: 7,
    },
  },
  tooltip: {
    y: {
      formatter: function (val) {
        return '$' + val + 'k';
      },
    },
    theme: 'dark',
  },
};

var chart = new ApexCharts(document.querySelector("#departments"), options);

chart.render();