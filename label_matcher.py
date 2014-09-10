'''
Script that finds all species records which match an image label on species, genus,
date, collection, state, and county. Due to an overhaul on how we treat species
images, it is no longer necessary to have image label info in two seperate records in the
database. The script provides a way to remove unneeded duplicates.

To work, this script needs to be run from "pnwmoths/app".
'''

import os
os.environ['DJANGO_SETTINGS_MODULE']='settings'
from species.models import Species, SpeciesRecord, SpeciesImage
from distutils.util import strtobool

# Create a list containing the desired fields from the input record
def make_data(record):
    record_data = [record.id, record.record_type, record.latitude, record.longitude, record.state, record.county, record.locality, record.elevation, record.date, record.collector, record.collection]
    
    # If the the field exists, change list entry to string representation
    # TODO: Figure out a way to change list elements without referring to them by index. This would improve readability.
    if record.state:
        record_data[4] = record.state.code
    if record.county:
        record_data[5] = record.county.name
    if record.collector:
        record_data[9] = record.collector.name
    if record.collection:
        record_data[10] = record.collection.name
        
    return map(str, record_data)

# Print out label and matching record in a nicely formatted grid
def print_grid(image, record):
    
    # Intialize data with everything that doesn't come from the actual records
    data = [
        ['', 'ID','Voucher Type', 'Latitude', 'Longitude', 'State', 'County', 'Locality', 'Elevation', 'Date', 'Collector', 'Collection'],
        ['Current Label:'],
        ['Matching Record:']
    ]
    
    # Add fields from both records to the data
    data[1].extend(make_data(image))
    data[2].extend(make_data(record))
    
    # Determine how wide each column in grid needs to be
    # Loop through each column
    for col_index in range(len(data[0])):
        col_width = 0
        
        # Loop through each row
        for row_index in range(len(data)):
            
            # If word at current position is longer in length than the current column width, save its length
            if len(data[row_index][col_index]) > col_width:
                col_width = len(data[row_index][col_index])
        
        # Loop through each word in column and set its width to the longest width found in column (plus 2)       
        for row_index in range(len(data)):
            data[row_index][col_index] = data[row_index][col_index].ljust(col_width+2)
    
    # Print each row
    for row in data:
        print "".join(row)

# Find all images for input species, and find records matching image labels        
def match_species(species_id):
    images = SpeciesImage.objects.all().filter(species=species_id)
    num_images = len(images)
    image_count = 0
    
    try:
        for image in images:
            image_count += 1
            print "Image %d of %d:" % (image_count, num_images)
            
            # Find records matching image label
            records = SpeciesRecord.objects.all().filter(
            species=species_id, year=image.record.year, month=image.record.month, day=image.record.day, state=image.record.state, county=image.record.county,collection=image.record.collection).exclude(
            id=image.record.id)
            
            if records:
                num_records = len(records)
                record_count = 0
                
                # For each matching record, print image label and record and ask user what they want to do
                for record in records:
                    record_count +=1
                    print "Match %d of %d:" % (record_count, num_records)
                    print_grid(image.record, record)
                    confirm = strtobool(raw_input("Delete current label and replace with this record? (yes/no) "))
                    
                    # Delete label and use matching record
                    if confirm:
                        image.record.delete()
                        image.record = record
                        image.save()
                        print "Original label deleted, and matching record now used \n"
                    else:
                        confirm = strtobool(raw_input("Replace current label with this record, but keep old label in database? (yes/no) "))
                        
                        # Change label to record, but don't delete label
                        if confirm:
                            image.record = record
                            image.save()
                            print "Matching record now used as label, and old label kept in database \n"
                        else:
                            print "No changes made \n"
            else:
                print "No records match image label \n"
                        
    except ValueError:
        print "Valid inputs are 'yes', 'y', 'no', and 'n'"

def main():
    running = True
    while running:
        try:
            option = raw_input("Enter 1 to find records for all species images, or 2 to examine images from a select species: ")
            print ''
            # Match labels for every species in database which has images
            if option == '1':
                all_species = SpeciesImage.objects.order_by('species__species').order_by('species__genus').exclude(species__isnull=True).exclude(record__isnull=True).values('species__id','species__genus', 'species__species').distinct()
                for species_image in all_species:
                    print species_image['species__genus'] + ' ' + species_image['species__species'] + " images:"
                    match_species(species_image['species__id'])
                running = False
                
            # Match labels for specific species        
            elif option == '2':
                name = raw_input("Enter species name: ")
                print ''
                in_genus, in_species = name.split()
                species_id = Species.objects.get(genus=in_genus, species=in_species).id
                match_species(species_id)
            
            else:
                print "Entered text '" + option + "' not a valid option. Please enter 1 or 2."
            
        except ValueError:
            print "Species name must be two words (genus species)"
        except Species.DoesNotExist:
            print "Species " + name + " not found in database"
        except KeyboardInterrupt:
            print "Bye!"
            running = False

if __name__ == "__main__":
    main()
