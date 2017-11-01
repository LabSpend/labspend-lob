import csv
import datetime
import lob
import os
import sys

# TODO: Get Sean's API Key
# lob.api_key = ''

success_csv_fields = [
    'lab_name',
    'id',
    'url',
    'address_line1',
    'address_line2',
    'address_city',
    'address_state',
    'address_zip',
    'product_name',
    'old_cost',
    'new_cost'
]

errors_csv_fields = ['error']

def create_from_address():
  try:
    from_address = lob.Address.create(
        name='Sean Seaver',
        company='Lab Spend',
        address_line1='PO Box 970751',
        address_line2='',
        address_city='Ypsilanti',
        address_state='MI',
        address_zip='48197',
        address_country='US'
    )

    return from_address
  except Exception as e:
      print('Error: ' + str(e))
      print('Failed to create from_address.')
      sys.exit(1)

if __name__=='__main__':

  # usage:
  #   python postcard.py input.csv
  #   logs to csv's in the output directory

  # Input check
  if len(sys.argv) < 2:
      print("Please provide an input CSV file as an argument.")
      print("usage: python letter.py <CSV_FILE>")
      sys.exit(1)

  input_filename = sys.argv[1]

  from_address = create_from_address()

  # create output directory
  output_dir = os.path.join('.',  'output')
  if not os.path.isdir(output_dir):
      os.mkdir(output_dir)

  timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

  try:
      output_dir = os.path.join(output_dir, timestamp)
      os.mkdir(output_dir)
  except Exception as e:
      print('Error: ' + str(e))
      print('Failed to create output directory. Aborting all sends.')
      sys.exit(1)

  # output csv names
  success_filename = os.path.join(output_dir, 'success.csv')
  errors_filename = os.path.join(output_dir, 'errors.csv')

  with open('templates/sample_labspend_front.html', 'r') as front_file,\
       open('templates/sample_labspend_back.html', 'r') as back_file:
      front_html = front_file.read()
      back_html = back_file.read()

  try:
      with open(input_filename, 'r') as input, \
           open(success_filename, 'w') as success, \
           open(errors_filename, 'w') as errors:

          # Print mode to screen
          mode = lob.api_key.split('_')[0]
          print('Sending postcards in ' + mode.upper() + ' mode.')

          input_csv = csv.DictReader(input)
          errors_csv_fields += input_csv.fieldnames

          success_csv = csv.DictWriter(success, fieldnames=success_csv_fields)
          errors_csv = csv.DictWriter(errors, fieldnames=errors_csv_fields)

          err_count = 0

          # Loop through input CSV rows
          for idx, row in enumerate(input_csv):
              # Create postcard from row
              try:
                  postcard = lob.Postcard.create(
                      to_address={
                          'name':            row['lab_name'] + ', ' + row['to[company]'],
                          'address_line1':   row['to[address_line1]'],
                          'address_line2':   row['to[address_line2]'],
                          'address_city':    row['to[address_city]'],
                          'address_state':   row['to[address_state]'],
                          'address_zip':     row['to[address_zip]'],
                          'address_country': 'US'
                      },
                      from_address=from_address,
                      size='4x6',
                      front=front_html,
                      back=back_html,
                      merge_variables={
                          'lab_name':        row['lab_name'],
                          'product_name':    row['product_name'],
                          'old_cost':        '$' + row['old_cost'],
                          'new_cost':        '$' + row['new_cost']
                      }
                  )
              except Exception as e:
                  error_row = {'error': e}
                  error_row.update(row)
                  errors_csv.writerow(error_row)
                  err_count += 1
                  sys.stdout.write('E')
                  sys.stdout.flush()
              else:
                # record successful send
                  success_csv.writerow({
                      'lab_name':      postcard.to_address.name,
                      'id':            postcard.id,
                      'url':           postcard.url,
                      'address_line1': postcard.to_address.address_line1,
                      'address_line2': postcard.to_address.address_line2,
                      'address_city':  postcard.to_address.address_city,
                      'address_state': postcard.to_address.address_state,
                      'address_zip':   postcard.to_address.address_zip
                  })

                  # Print success
                  sys.stdout.write('.')
                  sys.stdout.flush()
  except Exception as e:
      print('Error: ' + str(e))
      sys.exit(1)

  print('')
  print('Done with ' + (str(err_count) if err_count else 'no') + ' errors.')
  print('Results written to ' + str(output_dir) + '.')
