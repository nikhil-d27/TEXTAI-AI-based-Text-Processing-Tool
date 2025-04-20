const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();

// Enable CORS and body parser
app.use(cors());
app.use(bodyParser.json());

// Database connection configuration
const db = mysql.createConnection({
    host: process.env.DB_HOST || '127.0.0.1',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || 'Root',
    database: process.env.DB_NAME || 'textai_db'
});
// Connect to database
db.connect((err) => {
    if (err) {
        console.error('Error connecting to database:', err);
        return;
    }
    console.log('Connected to MySQL database');
});

// Handle contact form submissions
app.post('/submit-contact', (req, res) => {
    const { name, email, message } = req.body;
    
    // Validate input
    if (!name || !email || !message) {
        return res.status(400).json({
            status: 'error',
            message: 'Please fill in all fields'
        });
    }

    // SQL query to insert contact form data
    const query = `
        INSERT INTO contacts (name, email, message) 
        VALUES (?, ?, ?)
    `;
    
    // Execute the query
    db.query(query, [name, email, message], (err, result) => {
        if (err) {
            console.error('Error saving contact:', err);
            return res.status(500).json({
                status: 'error',
                message: 'An error occurred while sending your message'
            });
        }
        
        res.json({
            status: 'success',
            message: 'Thank you for contacting us! We will get back to you soon.'
        });
    });
});

// Start server
const PORT = process.env.PORT || 5503;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
}); 

