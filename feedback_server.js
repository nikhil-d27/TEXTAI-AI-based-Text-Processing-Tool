const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();

// Enable CORS and body parser
app.use(cors());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// Database configuration
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
    
    // Create database if it doesn't exist
    db.query('CREATE DATABASE IF NOT EXISTS textai', (err) => {
        if (err) throw err;
        
        // Use the database
        db.query('USE textai_db', (err) => {
            if (err) throw err;
            
            // Create feedback table if it doesn't exist
            const createTableQuery = `
                CREATE TABLE IF NOT EXISTS feedback (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    feedback_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            `;
            
            db.query(createTableQuery, (err) => {
                if (err) throw err;
                console.log('Feedback table ready');
            });
        });
    });
});

// Endpoint to handle feedback submission
app.post('/submit_feedback', (req, res) => {
    const feedbackText = req.body.feedback;
    
    if (!feedbackText) {
        return res.status(400).json({
            status: 'error',
            message: 'No feedback provided'
        });
    }

    const query = 'INSERT INTO feedback (feedback_text) VALUES (?)';
    
    db.query(query, [feedbackText], (err, result) => {
        if (err) {
            console.error('Error saving feedback:', err);
            return res.status(500).json({
                status: 'error',
                message: 'An error occurred while saving your feedback'
            });
        }
        
        res.json({
            status: 'success',
            message: 'Thank you for your feedback!'
        });
    });
});

// Start server
const PORT = process.env.PORT || 5504;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
}); 
