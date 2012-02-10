import smtplib

from email.mime.text import MIMEText

def send_email(f,t,s,c):
    msg = MIMEText(c)

    msg['Subject'] = s
    msg['From'] = f
    msg['To'] = t

    s = smtplib.SMTP('smtp-unencrypted.stanford.edu')
    s.sendmail(f, [t], msg.as_string())
    s.quit()
