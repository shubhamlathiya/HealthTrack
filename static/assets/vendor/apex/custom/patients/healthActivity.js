var options = {
  series: [{
    name: 'Health Activity',
    data: [80, 50, 30, 40, 90, 20],
  }],
  chart: {
    height: 350,
    type: 'radar',
    toolbar: {
      show: false,
    },
  },
  dataLabels: {
    enabled: false,
  },
  yaxis: {
    stepSize: 20
  },
  colors: ["#566fe2", "#D3CFFB", "#DFDCFC"],
  xaxis: {
    categories: ['Walking', 'Sleeping', 'Yoga', 'Gym', 'Playing', 'swimming']
  }
};

var chart = new ApexCharts(document.querySelector("#healthActivity"), options);
chart.render();