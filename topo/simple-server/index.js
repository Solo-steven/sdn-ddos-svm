const express = require('express');
const app = express();
const path = require('path');

app.use(express.json());
app.use(express.urlencoded());
app.use(express.static(path.resolve(__dirname, 'static')))

app.listen(3000, () => {
    console.log("Web Server is on")
});