from email import message
import logging
import azure.functions as func
import psycopg2
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def main(msg: func.ServiceBusMessage):

    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info('Python ServiceBus queue trigger processed message: %s',notification_id)

    # TODO: Update connection settings
    pgConn = psycopg2.connect(
        host = "<>",
        database ="<>" ,
        user = "<>",
        password = "<>"
    )

    cursor = pgConn.cursor()
    logging.info("Successfully connected to database.")

    try:
        # Get notification message and subject from database using the notification_id
        selectNotificationQry = f"SELECT message, subject FROM notification WHERE id={str(notification_id)}"
        cursor.execute(selectNotificationQry)
        message, subj = cursor.fetchone()
        logging.info(f"Notification ID {str(notification_id)} \n\t Subject: {subj} \n\t Message: {message}")

        # Get attendees email and name
        getAttendeeQry = f"SELECT first_name, last_name, email FROM attendee;"
        cursor.execute(getAttendeeQry)
        allAttendees = cursor.fetchall()

        # TODO: Loop through each attendee and send an email with a personalized subject
        for curAttendee in allAttendees:
            firstName = curAttendee[0]
            surName = curAttendee[1]
            emailAddress = curAttendee[2]
            email_subject = f"Hello {firstName} | {subj} "
            print(email_subject)

            #TODO Update sender email for notifications 
            mail = Mail(
                from_email = '<>',
                to_emails = emailAddress,
                subject = email_subject,
                plain_text_content = message
            )
            try:
                #TODO Update send grid API key for authenticstion 
                sg = SendGridAPIClient('<>')
                response = sg.send(mail)
                print(response.status_code)
                print(response.body)
                print(response.headers)
            except Exception as e:
                print(str(e))     

        # Update the notification table by setting the completed date and updating the status with the total number of attendees notified
        timeNow = datetime.now()
        status = f"Notified {str(len(allAttendees))} attendees"
        updateNotificationQry = f"UPDATE notification SET status='{status}', completed_date='{timeNow}' WHERE id={notification_id};"
        cursor.execute(updateNotificationQry)
        pgConn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
        pgConn.rollback()
    finally:
        # Close connection
        cursor.close()
        pgConn.close()
        logging.info("PostgresSQL connection closed.")
