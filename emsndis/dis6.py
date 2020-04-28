"""
dis6.py
~~~~~~~~

Implementation of the IEEE DIS standard Protocol Version 6.

References:

[1] IEEE. (1995). IEEE 1278.1-1995 Standard for distributed
    interactive simulation. IEEE.
[2] IEEE. (1998). IEEE 1278.1a-1998 Standard for distributed
    interactive simulation. IEEE.
"""

import struct
from io import BytesIO
from bitstring import BitArray

# Field encodings
# ---------------

pduHeaderEncoding =  [
    ['protocolVersion','8-bit_enumeration'],
    ['excerciseId','8-bit_unsigned_integer'],
    ['pduType','8-bit_enumeration'],
    ['protocolFamily','8-bit_enumeration'],
    ['timestamp','32-bit_unsigned_integer'],
    ['length','16-bit_unsigned_integer'],
    ['padding','16-bits'],
]

pduHeaderEncoding = [
    ['protocolVersion','8-bit_enumeration'],
    ['excerciseId','8-bit_unsigned_integer'],
    ['pduType','8-bit_enumeration'],
    ['protocolFamily','8-bit_enumeration'],
    ['timestamp','32-bit_unsigned_integer'],
    ['length','16-bit_unsigned_integer'],
    ['padding','16-bit_unsigned_integer'],
]

entityIdEncoding = [
    ['site','16-bit_unsigned_integer'],
    ['application','16-bit_unsigned_integer'],
    ['entity','16-bit_unsigned_integer']
]

entityTypeEncoding = [
    ['entityKind','8-bit_enumeration'],
    ['domain','8-bit_enumeration'],
    ['country','16-bit_enumeration'],
    ['category','8-bit_enumeration'],
    ['subcategory','8-bit_enumeration'],
    ['specific','8-bit_enumeration'],
    ['extra','8-bit_enumeration']
]

entityLinearVector32Encoding = [
    ['x','32-bit_float'],
    ['y','32-bit_float'],
    ['z','32-bit_float'],
]

entityLinearVector64Encoding = [
    ['x','64-bit_float'],
    ['y','64-bit_float'],
    ['z','64-bit_float'],
]

entityAngularVector32Encoding = [
    ['psi','32-bit_float'],
    ['theta','32-bit_float'],
    ['phi','32-bit_float'],
]


deadReckoningParametersEncoding = [
    ['deadReckoningAlgorithm','8-bit_enumeration'],
    ['otherParameters','120-bits'],
    ['entityLinearAcceleration',entityLinearVector32Encoding],
    ['entityAngularVelocity',entityAngularVector32Encoding]
]

entityMarkingEncoding = [
    ['characterSet','8-bit_enumeration'],
    ['characters','11x8-bit_unsigned_integer']

]

clockTimeEncoding = [
    ['hour','32-bit_integer'],
    ['timePastHour','32-bit_unsigned_integer'],
]

# PDU encodings
# ------------- 

entityStatePduEncoding = [
    ['pduHeader',pduHeaderEncoding],
    ['entityId',entityIdEncoding],
    ['forceId','8-bit_enumeration'],
    ['numberOfArticulationParameters','8-bit_unsigned_integer'],
    ['entityType',entityTypeEncoding],
    ['alternativeEntityType',entityTypeEncoding],
    ['entityLinearVelocity',entityLinearVector32Encoding],
    ['entityLocation',entityLinearVector64Encoding],
    ['entityOrientation',entityAngularVector32Encoding],
    ['entityAppearance','32-bits'],
    ['deadReckoningParameters',deadReckoningParametersEncoding],
    ['entityMarking',entityMarkingEncoding],
    ['capabilities','32xboolean']
]

startPduEncoding = [
    ['pduHeader',pduHeaderEncoding],
    ['originatingEntityId',entityIdEncoding],
    ['receivingEntityId',entityIdEncoding],
    ['realWorldTime',clockTimeEncoding],
    ['simulationTime',clockTimeEncoding],
    ['requestId','32-bit_unsigned_integer'],
]

stopPduEncoding = [
    ['pduHeader',pduHeaderEncoding],
    ['originatingEntityId',entityIdEncoding],
    ['receivingEntityId',entityIdEncoding],
    ['realWorldTime',clockTimeEncoding],
    ['reason','8-bit_enumeration'],
    ['frozenBehavior','8-bit_enumeration'],
    ['padding','16-bits'],
    ['requestId','32-bit_unsigned_integer'],
]

# Map of PDU types to PDU encodings
pdu_encodings = {
    1:entityStatePduEncoding,
    13:startPduEncoding,
    14:stopPduEncoding,
}

# (Format, Size in Bytes)
format_strings_dictionary = {
    '8-bit_enumeration':('B',1),
    '16-bit_enumeration':('>H',2),
    '8-bit_integer':('b',1),
    '8-bit_unsigned_integer':('B',1),
    '16-bit_integer':('>h',2),
    '16-bit_unsigned_integer':('>H',2),
    '32-bit_integer':('>i',4),
    '32-bit_unsigned_integer':('>I',4),
    '64-bit_integer':('>q',8),
    '64-bit_unsigned_integer':('>Q',8),
    '16-bit_float':('>e',2),
    '32-bit_float':('>f',4),
    '64-bit_float':('>d',8),
}


def _parse_encoding(raw_encoding):
    """Parses the encoding description.

    Returns
    -------
    (num, rep, size)
        num: number of repetitions
        rep: representation
        size: size of the representation in bytes
        
    """
    # Number of repetitions
    num = 1
    if 'x' in raw_encoding:
        i = raw_encoding.find('x')
        num = int(raw_encoding[0:i])
        encoding = raw_encoding[i+1:]
    else:
        encoding = raw_encoding
    # Reprsentation
    if 'bits' in encoding:
        i = encoding.find('-')
        size = int(int(encoding[0:i])//8)
        rep = 'bits'
    elif 'boolean' in encoding:
        rep = 'boolean'
        size = int(num//8)
        num = 1
    else:
        rep, size = format_strings_dictionary[encoding]
    return (num, rep, size)

def _serialize_variable(stream, value, encoding, pdu_length):
    """Serialize a variable into a binary stream.
    """
    num, rep, size = _parse_encoding(encoding)
    if rep == 'bits':
        _to_bytes = lambda v: BitArray('0b' + v).bytes
    elif rep == 'boolean':
        _to_bytes = lambda v: BitArray('0b'+''.join(['1' if i else '0' for i in v])).bytes
    else:
        _to_bytes = lambda v: struct.pack(rep, v)

    if num == 1:
        value = [value]
 
    for i in range(num):
        val = _to_bytes(value[i])
        pdu_length.append(len(val))
        stream.write(val)
   # return stream

def _serialize_field(stream, field_values, field_encoding, pdu_length):
    """ Serialize a field into a binary stream.
    """
    for (name, encoding) in field_encoding:
        value = field_values[name]
        if type(encoding) is str:
            _serialize_variable(stream, value, encoding, pdu_length)
        else:
            _serialize_field(stream,value, encoding, pdu_length)
    return stream

def serialize(pdu):
    """Serialize a PDU dict into a binary stream.
        
    Usage
    -----
    pdu = {
        'pduHeader':{
            'protocolVersion': 5,
            'excerciseId': 1,
            'pduType': 1,
            'protocolFamily': 1,
            'timestamp': 0,
            'length':10,
            'padding': 0,
        }
    }
    stream = serialize_pdu(pdu)
    """
    stream = BytesIO()
    pdu_length = []
    pduType = pdu['pduHeader']['pduType']
    
    if pduType not in pdu_encodings:
        raise Exception(f"Error: PDU type {pduType} is not in the list of PDU encodings.")

    for (field_name, field_encoding) in pdu_encodings[pduType]:
        if type(field_encoding) is str:
            _serialize_variable(
                stream,
                pdu[field_name],
                field_encoding,
                pdu_length
                )
        else:
            _serialize_field(
                stream,
                pdu[field_name],
                field_encoding,
                pdu_length
                )
        #print(f'{field_name} : {sum(pdu_length)*8}')
        pdu_length = []
    return stream

def _deserialize_variable(stream, name, encoding):
    """ Deserialize a variable into a dict.
    """    
    num, rep, size = _parse_encoding(encoding)
    values = []
    for i in range(num):
        if rep == 'bits':
            val = BitArray(stream.read(size)).bin
            values.append(val)
        elif rep == 'boolean':
            val = BitArray(stream.read(size)).bin
            vals = [True if i == '1' else False for i in val]
            values.append(vals)
        else:
            values.append(struct.unpack(rep,stream.read(size))[0])
    value = values[0] if num == 1 else values
    return {name: value}
 
def _deserialize_field(stream, field_name, field_encoding):
    """ Deserialize a field into a dict.
    """
    field_dict = {}
    for (var_name, var_encoding) in field_encoding:
        if type(var_encoding) is str:
            var_dict = _deserialize_variable(stream, var_name, var_encoding) 
        else:
            var_dict = _deserialize_field(stream, var_name, var_encoding)
        field_dict.update(var_dict)
    return {field_name: field_dict}

def deserialize(data):
    """Deserialize a data package into a PDU dict.
    
    Usage
    -------
    pdu = deserialize(data)

    """
    pdu = {}
    stream = BytesIO(data)

    # Try to deserialize the PDU header
    pdu = _deserialize_field(stream,'pduHeader',pduHeaderEncoding)

    # Check the PDU's protocol version is 5
    pduProtocolVersion = pdu['pduHeader']['protocolVersion']
    #if pduProtocolVersion != 5:
    #    raise Exception(f'Deserialized PDU is {pduProtocolVersion}, it shold be 5.')

    # Success, try to deserialize the rest
    pduType = pdu['pduHeader']['pduType']
    #
    if pduType in pdu_encodings:
        #    raise Exception(f"PDU type {pduType} is not in the list of PDU encodings.")
        for (field_name, field_encoding) in pdu_encodings[pduType][1:]:
            if type(field_encoding) is str:
                var_dict = _deserialize_variable(
                    stream,
                    field_name,
                    field_encoding
                    )
                pdu.update(var_dict)
            else:
                field_dict = _deserialize_field(
                    stream,
                    field_name,
                    field_encoding
                    )
                pdu.update(field_dict)
        return pdu
    else:
        return pdu

if __name__ == '__main__':
    pdu_example = {
        'pduHeader': {
            'protocolVersion': 5,
            'excerciseId': 1,
            'pduType':1,
            'protocolFamily': 2,
            'timestamp': 10,
            'length': 10,
            'padding':0,
        },
        'entityId': {
            'site': 1,
            'application':2,
            'entity':1,
        },
        'forceId':1,
        'numberOfArticulationParameters':0,
        'entityType': {
            'entityKind':1,
            'domain':2,
            'country':1,
            'category':3,
            'subcategory':2,
            'specific':1,
            'extra':1
        },
        'alternativeEntityType': {
            'entityKind':1,
            'domain':2,
            'country':1,
            'category':3,
            'subcategory':2,
            'specific':1,
            'extra':1
        },
        'entityLinearVelocity': {
            'x':1,
            'y':2,
            'z':3,
        },
        'entityLocation': {
            'x':1.99,
            'y':2,
            'z':3,
        },
        'entityOrientation': {
            'psi':1,
            'theta':2,
            'phi':3,
        },
        'entityMarking': {
            'characterSet':1,
            'characters':[33]*11,
        },
        'deadReckoningParameters':{
            'deadReckoningAlgorithm':1,
            'otherParameters': '1'*120,
            'entityLinearAcceleration': {
                'x':1,
                'y':2,
                'z':3,
            },
            'entityAngularVelocity':{
                'psi':1,
                'theta':2,
                'phi':3,
            },
        },
        'entityAppearance': '1'*32,
        'capabilities':[False]*32,
    }
   
    s = serialize(pdu_example)
    #len(s)
    data = s.getvalue()
    print(f'Print {len(data)}')
    pdu = deserialize(data)
    print(pdu)
    print(pdu == pdu_example)
