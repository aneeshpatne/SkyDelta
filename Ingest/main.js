const res = await fetch("http://192.168.1.50/sensors_v2");

const data = await res.json();

console.log(data);
